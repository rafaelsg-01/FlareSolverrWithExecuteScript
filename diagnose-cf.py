r"""
diagnose-cf.py - Introspecciona a pagina de desafio da Cloudflare.

Lista TODOS os inputs, iframes, o estado do widget Turnstile, tenta entrar
nos iframes (inclusive o cross-origin da challenges.cloudflare.com), faz o
clique (TAB+SPACE, igual o FlareSolverr) e mostra o ANTES/DEPOIS, tirando
screenshots em ./cf-diag/.

Uso (dentro da pasta do projeto, com o venv):
  # navegador VISIVEL (voce ve a tela):
  $env:HEADLESS="false"; .\.venv\Scripts\python.exe diagnose-cf.py

  # igual a VM (headless real, via maxOptimization):
  $env:HEADLESS="true"; $env:MAXOPT="true"; .\.venv\Scripts\python.exe diagnose-cf.py

  # url diferente:
  $env:URL="https://redecanais.uk/robots.txt"; .\.venv\Scripts\python.exe diagnose-cf.py
"""
import os
import sys
import time
import json
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import utils
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

URL = os.environ.get("URL", "https://redecanais.uk/templates/echo/css/custom.css#_execScript_setHeadersRedeCanais")
MAXOPT = os.environ.get("MAXOPT", "false").lower() == "true"
# injeta o firstScript (fetch /che + service worker) igual o app -> seta RCSESS/RCIP
USE_FIRSTSCRIPT = os.environ.get("FIRSTSCRIPT", "true").lower() == "true"
# proxy (mesmas envs do app): PROXY_URL http://host:porta + PROXY_USERNAME + PROXY_PASSWORD
PROXY_URL = os.environ.get("PROXY_URL") or None
PROXY_USERNAME = os.environ.get("PROXY_USERNAME") or None
PROXY_PASSWORD = os.environ.get("PROXY_PASSWORD") or None

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cf-diag")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "log.txt"), "w", encoding="utf-8")


def log(*a):
    line = " ".join(str(x) for x in a)
    stamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(stamp, line)
    LOG.write(stamp + " " + line + "\n")
    LOG.flush()


# JS que resume o estado da pagina (main document)
INTROSPECT_JS = r"""
const q = (s) => [...document.querySelectorAll(s)];
return {
  title: document.title,
  url: location.href,
  cookies_len: document.cookie.length,
  inputs: q('input').map(i => ({type:i.type, name:i.name, id:i.id, value:(i.value||'').slice(0,40)})),
  iframes: q('iframe').map(f => ({src:f.src, id:f.id, name:f.name, w:f.offsetWidth, h:f.offsetHeight, visible:!!(f.offsetWidth||f.offsetHeight)})),
  buttons: q('button, input[type=button], input[type=submit]').map(b => ({tag:b.tagName, text:(b.innerText||b.value||'').slice(0,40), id:b.id})),
  ncOB5_html: (document.querySelector('#ncOB5')||{}).outerHTML,
  cf_widget_state: {
    verifying: !!document.querySelector('#nLfsA2') && (document.querySelector('#nLfsA2').offsetParent!==null),
    success_div_hidden: (document.querySelector('#DGcC5')||{}).style ? document.querySelector('#DGcC5').style.display : null
  },
  bodyText: (document.body ? document.body.innerText : '').slice(0,160)
};
"""


def snap(driver, tag):
    try:
        path = os.path.join(OUT, f"shot-{tag}.png")
        driver.get_screenshot_as_base64()  # forca render
        driver.save_screenshot(path)
        log(f"  [screenshot] {path}")
    except Exception as e:
        log(f"  [screenshot ERRO] {e}")


def dump_state(driver, tag):
    log(f"===== ESTADO [{tag}] =====")
    try:
        st = driver.execute_script(INTROSPECT_JS)
    except Exception as e:
        log(f"  execute_script falhou: {e}")
        return None
    log(f"  title   : {st['title']}")
    log(f"  url     : {st['url']}")
    log(f"  inputs (main doc): {len(st['inputs'])}")
    for i in st["inputs"]:
        log(f"     - input type={i['type']} name={i['name']} id={i['id']} value={i['value']}")
    log(f"  iframes : {len(st['iframes'])}")
    for f in st["iframes"]:
        log(f"     - iframe src={f['src'][:90]} id={f['id']} {f['w']}x{f['h']} visible={f['visible']}")
    log(f"  buttons : {len(st['buttons'])}")
    for b in st["buttons"]:
        log(f"     - button <{b['tag']}> text='{b['text']}' id={b['id']}")
    log(f"  #ncOB5  : {str(st['ncOB5_html'])[:200]}")
    log(f"  bodyText: {st['bodyText']!r}")
    # cookies do selenium (aqui pega httpOnly tambem, ex cf_clearance)
    cks = [c["name"] for c in driver.get_cookies()]
    log(f"  cookies (selenium): {cks}")
    return st


def inspect_iframes(driver):
    """Tenta ENTRAR em cada iframe e listar inputs/botoes de dentro (inclusive o Turnstile)."""
    log("===== DENTRO DOS IFRAMES =====")
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    log(f"  {len(frames)} iframe(s) no documento principal")
    for idx, fr in enumerate(frames):
        try:
            src = fr.get_attribute("src") or ""
            driver.switch_to.frame(fr)
            log(f"  -> ENTROU iframe #{idx} src={src[:90]}")
            try:
                info = driver.execute_script(r"""
                  const q=(s)=>[...document.querySelectorAll(s)];
                  return {
                    title: document.title,
                    inputs: q('input').map(i=>({type:i.type,name:i.name,id:i.id})),
                    buttons: q('button,[role=button],input[type=button],input[type=checkbox]').map(b=>({tag:b.tagName,type:b.type||'',text:(b.innerText||b.value||b.ariaLabel||'').slice(0,40),id:b.id})),
                    labels: q('label').map(l=>l.innerText.slice(0,40)),
                    hasShadow: !!document.querySelector('*') && [...document.querySelectorAll('*')].some(e=>e.shadowRoot),
                    html: document.documentElement.outerHTML.slice(0,300)
                  };
                """)
                log(f"       titulo interno: {info['title']}")
                log(f"       inputs internos: {info['inputs']}")
                log(f"       buttons/checkbox internos: {info['buttons']}")
                log(f"       labels: {info['labels']}")
                log(f"       tem shadowRoot: {info['hasShadow']}")
                log(f"       html(300): {info['html']}")
            except Exception as e:
                log(f"       (nao consegui ler dentro: {e})")
            # tenta iframes aninhados (Turnstile usa iframe dentro de iframe)
            nested = driver.find_elements(By.TAG_NAME, "iframe")
            for j, nf in enumerate(nested):
                try:
                    nsrc = nf.get_attribute("src") or ""
                    driver.switch_to.frame(nf)
                    log(f"       -> iframe ANINHADO #{j} src={nsrc[:90]}")
                    ninfo = driver.execute_script(r"""
                      const q=(s)=>[...document.querySelectorAll(s)];
                      return {inputs:q('input').map(i=>({type:i.type,id:i.id})),
                              cbs:q('input[type=checkbox]').length,
                              text:(document.body?document.body.innerText:'').slice(0,120)};
                    """)
                    log(f"          inputs: {ninfo['inputs']} checkboxes: {ninfo['cbs']} text={ninfo['text']!r}")
                    driver.switch_to.parent_frame()
                except Exception as e:
                    log(f"          (aninhado erro: {e})")
                    driver.switch_to.parent_frame()
        except Exception as e:
            log(f"  -> iframe #{idx} nao acessivel: {e}")
        finally:
            driver.switch_to.default_content()


def main():
    log(f"URL={URL}")
    log(f"HEADLESS={os.environ.get('HEADLESS','true')}  MAXOPT={MAXOPT}  FIRSTSCRIPT={USE_FIRSTSCRIPT}")
    utils.get_current_platform()
    first_script = None
    if USE_FIRSTSCRIPT:
        import js_first_script
        first_script = js_first_script.Js_firstScriptImport
        log("firstScript INJETADO (igual o app: fetch /che + service worker)")

    proxy = None
    if PROXY_URL:
        proxy = {"url": PROXY_URL}
        if PROXY_USERNAME or PROXY_PASSWORD:
            proxy["username"] = PROXY_USERNAME
            proxy["password"] = PROXY_PASSWORD
        log(f"PROXY ATIVO: {PROXY_URL}  user={PROXY_USERNAME}")

    driver = utils.get_webdriver(proxy=proxy, first_script=first_script, max_optimization=MAXOPT)
    try:
        # confere o IP de saida (prova que o proxy esta ativo e de qual pais)
        if proxy:
            try:
                driver.get("https://api.ipify.org?format=json")
                time.sleep(1)
                ip_txt = driver.find_element(By.TAG_NAME, "body").text
                log(f"IP DE SAIDA (via proxy): {ip_txt}")
            except Exception as e:
                log(f"nao consegui checar IP de saida: {e}")

        log("navegando...")
        driver.get(URL)
        time.sleep(2)

        dump_state(driver, "00-inicial")
        snap(driver, "00-inicial")
        inspect_iframes(driver)

        # ---- clique igual o FlareSolverr (TAB + SPACE as cegas) ----
        log("===== CLICANDO (TAB + SPACE, igual FlareSolverr) =====")
        try:
            ActionChains(driver).pause(3).send_keys(Keys.TAB).pause(1).send_keys(Keys.SPACE).perform()
            log("  TAB+SPACE enviado")
        except Exception as e:
            log(f"  erro no clique: {e}")
        driver.switch_to.default_content()
        snap(driver, "01-logo-apos-clique")
        dump_state(driver, "01-logo-apos-clique")

        # ---- acompanha por ~60s o que muda ----
        solved = False
        for i in range(20):
            time.sleep(3)
            st = dump_state(driver, f"loop-{i:02d}")
            snap(driver, f"loop-{i:02d}")
            cks = [c["name"] for c in driver.get_cookies()]
            title = (st or {}).get("title", "")
            if "cf_clearance" in cks or (title and "just a moment" not in title.lower() and "moment" not in title.lower()):
                log(f">>> MUDOU! title='{title}' cookies={cks}")
                solved = True
                break

        # ---- DEPOIS da verificacao: recarrega pra pegar o conteudo REAL ----
        if solved:
            log("===== APOS VERIFICACAO: recarregando pra sair da tela de 'carregando' =====")
            time.sleep(2)
            # igual o app: espera o firstScript terminar (fetch /che + service worker) antes de recarregar
            try:
                driver.execute_script("return window._waitNewPromise;")
                log("  window._waitNewPromise aguardado (handshake /che + sw)")
            except Exception as e:
                log(f"  window._waitNewPromise indisponivel: {e}")
            driver.get(URL)   # igual o location.reload() que o FlareSolverr faz
            time.sleep(4)
            st_after = dump_state(driver, "100-apos-verificacao")
            snap(driver, "100-apos-verificacao")
            body = (driver.page_source or "").replace("\n", " ")
            log("  CONTEUDO REAL (primeiros 300 chars): " + body[:300])

        log("===== FINAL =====")
        dump_state(driver, "99-final")
        snap(driver, "99-final")
        html_path = os.path.join(OUT, "final.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        log(f"HTML final salvo em {html_path}")
        log("RESOLVEU (e recarregou o conteudo real, ver shot-100)!" if solved
            else "NAO resolveu no tempo observado (continuaria no loop - este e o caso da VM).")
    finally:
        try:
            if utils.PLATFORM_VERSION == "nt":
                driver.close()
            driver.quit()
        except Exception:
            pass
        LOG.close()


if __name__ == "__main__":
    main()
