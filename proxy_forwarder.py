"""
proxy_forwarder.py - Encaminhador de proxy com autenticacao.

O undetected_chromedriver NAO aplica a extensao de auth do Chrome, mas RESPEITA
--proxy-server. Entao apontamos o Chrome para este encaminhador local (sem auth) e
ele repassa pro proxy de verdade (DataImpulse etc.) injetando o Proxy-Authorization.

Fluxo:  Chrome --proxy-server=http://127.0.0.1:8899  ->  este forwarder  ->  UPSTREAM (com auth)

Config por variaveis de ambiente:
  FORWARD_LISTEN_HOST   (default 127.0.0.1)
  FORWARD_LISTEN_PORT   (default 8899)
  UPSTREAM_HOST         (ex: gw.dataimpulse.com)
  UPSTREAM_PORT         (ex: 823)
  UPSTREAM_USER         (ex: c0e8e9f9167a53bb6da8__cr.br)
  UPSTREAM_PASS         (ex: 3ab60d02ecdfd201)

Sem dependencias externas (asyncio puro).
"""
import asyncio
import base64
import logging
import os
import sys

LISTEN_HOST = os.environ.get("FORWARD_LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("FORWARD_LISTEN_PORT", "8899"))
UP_HOST = os.environ.get("UPSTREAM_HOST", "")
UP_PORT = int(os.environ.get("UPSTREAM_PORT", "0") or "0")
UP_USER = os.environ.get("UPSTREAM_USER", "")
UP_PASS = os.environ.get("UPSTREAM_PASS", "")

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [forwarder] %(message)s",
    level=os.environ.get("FORWARD_LOG_LEVEL", "INFO").upper(),
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("forwarder")

AUTH_HEADER = "Basic " + base64.b64encode(f"{UP_USER}:{UP_PASS}".encode()).decode()


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception:
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def handle_client(cr: asyncio.StreamReader, cw: asyncio.StreamWriter):
    up_writer = None
    try:
        request_line = await cr.readline()
        if not request_line:
            cw.close()
            return

        # le os headers do cliente (ate linha em branco)
        header_lines = []
        while True:
            line = await cr.readline()
            if line in (b"\r\n", b"\n", b""):
                break
            header_lines.append(line)

        parts = request_line.split()
        if len(parts) < 3:
            cw.close()
            return
        method = parts[0].decode("latin1").upper()
        target = parts[1].decode("latin1")

        # abre conexao com o upstream
        try:
            up_reader, up_writer = await asyncio.wait_for(
                asyncio.open_connection(UP_HOST, UP_PORT), timeout=30
            )
        except Exception as e:
            log.warning(f"falha ao conectar no upstream {UP_HOST}:{UP_PORT}: {e}")
            cw.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            await cw.drain()
            cw.close()
            return

        if method == "CONNECT":
            # HTTPS: abre o tunel no upstream com auth
            req = (
                f"CONNECT {target} HTTP/1.1\r\n"
                f"Host: {target}\r\n"
                f"Proxy-Authorization: {AUTH_HEADER}\r\n"
                f"Proxy-Connection: keep-alive\r\n\r\n"
            )
            up_writer.write(req.encode("latin1"))
            await up_writer.drain()

            status_line = await up_reader.readline()
            # consome o resto dos headers do upstream ate linha em branco
            while True:
                l = await up_reader.readline()
                if l in (b"\r\n", b"\n", b""):
                    break

            if b" 200 " in status_line or status_line.startswith(b"HTTP/1.1 200") or status_line.startswith(b"HTTP/1.0 200"):
                cw.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
                await cw.drain()
                await asyncio.gather(_pipe(cr, up_writer), _pipe(up_reader, cw))
            else:
                log.warning(f"upstream recusou CONNECT {target}: {status_line!r}")
                cw.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await cw.drain()
                cw.close()
        else:
            # HTTP simples (target em forma absoluta http://...): repassa injetando auth
            out = bytearray()
            out += request_line
            out += b"Proxy-Authorization: " + AUTH_HEADER.encode("latin1") + b"\r\n"
            for hl in header_lines:
                # remove Proxy-Connection do cliente pra evitar conflito
                if hl.lower().startswith(b"proxy-connection"):
                    continue
                out += hl
            out += b"\r\n"
            up_writer.write(bytes(out))
            await up_writer.drain()
            await asyncio.gather(_pipe(cr, up_writer), _pipe(up_reader, cw))
    except Exception as e:
        log.debug(f"erro no handle_client: {e}")
    finally:
        try:
            cw.close()
        except Exception:
            pass
        if up_writer is not None:
            try:
                up_writer.close()
            except Exception:
                pass


async def main():
    if not UP_HOST or not UP_PORT:
        log.error("UPSTREAM_HOST/UPSTREAM_PORT nao configurados. Encerrando.")
        sys.exit(1)
    server = await asyncio.start_server(handle_client, LISTEN_HOST, LISTEN_PORT)
    log.info(f"encaminhando {LISTEN_HOST}:{LISTEN_PORT}  ->  {UP_HOST}:{UP_PORT} (user={UP_USER})")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
