#!/bin/sh
# Entrypoint do container: sobe o encaminhador de proxy (se configurado) e depois o FlareSolverr.
# Se UPSTREAM_HOST nao estiver setado, roda so o FlareSolverr (comportamento antigo, sem proxy).

if [ -n "$UPSTREAM_HOST" ]; then
  echo "[start] Subindo proxy_forwarder -> $UPSTREAM_HOST:$UPSTREAM_PORT (listen 127.0.0.1:${FORWARD_LISTEN_PORT:-8898})"
  python -u /app/proxy_forwarder.py &
  # da um tempinho pro forwarder abrir a porta antes do Chrome tentar usar
  sleep 1
else
  echo "[start] UPSTREAM_HOST nao definido -> rodando sem proxy"
fi

exec python -u /app/flaresolverr.py
