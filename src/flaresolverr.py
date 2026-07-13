import json
import logging
import os
import sys
import threading

import certifi
from bottle import run, response, Bottle, request, ServerAdapter

from bottle_plugins.error_plugin import error_plugin
from bottle_plugins.logger_plugin import logger_plugin
from bottle_plugins import prometheus_plugin
from dtos import V1RequestBase
import flaresolverr_service
import utils
import js_first_script

env_proxy_url = os.environ.get('PROXY_URL', None)
env_proxy_username = os.environ.get('PROXY_USERNAME', None)
env_proxy_password = os.environ.get('PROXY_PASSWORD', None)
env_token = os.environ.get('TOKEN_PROXY_WEB', None)
env_initial_url = os.environ.get('INITIAL_URL', None)
# Se 'false', o warm-up (session01 + request no redecanais via proxy) NAO roda no boot;
# passa a ser feito sob demanda, na 1a request externa autenticada (modo hibernacao).
env_warmup_on_boot = os.environ.get('WARMUP_ON_BOOT', 'true').lower() == 'true'


def validate_token():
    """
    Validate token from query parameter
    """
    if env_token is None:
        return True
    token = request.query.get('token')
    if token != env_token:
        response.status = 401
        response.content_type = 'application/json'
        return False
    return True


class JSONErrorBottle(Bottle):
    """
    Handle 404 errors
    """
    def default_error_handler(self, res):
        response.content_type = 'application/json'
        return json.dumps(dict(error=res.body, status_code=res.status_code))


app = JSONErrorBottle()


@app.route('/')
def index():
    """
    Show welcome message
    """
    if not validate_token():
        return json.dumps(dict(error='Unauthorized', status_code=401))
    res = flaresolverr_service.index_endpoint()
    return utils.object_to_dict(res)


@app.route('/health')
def health():
    """
    Healthcheck endpoint.
    This endpoint is special because it doesn't print traces
    """
    if not validate_token():
        return json.dumps(dict(error='Unauthorized', status_code=401))
    res = flaresolverr_service.health_endpoint()
    return utils.object_to_dict(res)


@app.post('/v1')
def controller_v1(request_json_internal=None):
    """
    Controller v1
    """
    if request_json_internal is None:
        if not validate_token():
            return json.dumps(dict(error='Unauthorized', status_code=401))
    data = request_json_internal or request.json or {}
    # Modo hibernacao: na 1a request externa de conteudo (token ja validado acima), faz o
    # warm-up (cria session01 + resolve o desafio) antes de processar. No-op se ja aquecido.
    if request_json_internal is None and data.get('cmd') in ('request.get', 'request.post'):
        ensure_warmup()
    if (('proxy' not in data or not data.get('proxy')) and env_proxy_url is not None and (env_proxy_username is None and env_proxy_password is None)):
        logging.info('Using proxy URL ENV')
        data['proxy'] = {"url": env_proxy_url}
    if (('proxy' not in data or not data.get('proxy')) and env_proxy_url is not None and (env_proxy_username is not None or env_proxy_password is not None)):
        logging.info('Using proxy URL, username & password ENVs')
        data['proxy'] = {"url": env_proxy_url, "username": env_proxy_username, "password": env_proxy_password}
    req = V1RequestBase(data)
    res = flaresolverr_service.controller_v1_endpoint(req)
    if res.__error_500__:
        response.status = 500
    return utils.object_to_dict(res)


_warmup_lock = threading.Lock()
_warmup_done = False


def run_initial_warmup():
    """Cria a session01 e faz o request inicial no redecanais (usa o proxy)."""
    if env_initial_url is None or env_initial_url == '':
        return

    logging.info('Creating initial session')
    Js_firstScript = js_first_script.Js_firstScriptImport

    initialSessionCreate = controller_v1(request_json_internal={
        "cmd": "sessions.create",
        "session": "session01",
        "maxOptimization": True,
        "firstScript": Js_firstScript
    })
    logging.info(f'Initial session created: {initialSessionCreate}')

    logging.info('Creating initial request')
    initialRequestGet = controller_v1(request_json_internal={
        "cmd": "request.get",
        "session": "session01",
        "url": env_initial_url,
        "maxTimeout": 240000,
        "configured": True
    })
    logging.info(f'Initial request completed: {initialRequestGet}')


def ensure_warmup():
    """Garante que o warm-up rodou uma vez so (thread-safe)."""
    global _warmup_done
    if _warmup_done:
        return
    with _warmup_lock:
        if _warmup_done:
            return
        run_initial_warmup()
        _warmup_done = True


if __name__ == "__main__":
    # check python version
    if sys.version_info < (3, 9):
        raise Exception("The Python version is less than 3.9, a version equal to or higher is required.")

    # fix for HEADLESS=false in Windows binary
    # https://stackoverflow.com/a/27694505
    if os.name == 'nt':
        import multiprocessing
        multiprocessing.freeze_support()

    # fix ssl certificates for compiled binaries
    # https://github.com/pyinstaller/pyinstaller/issues/7229
    # https://stackoverflow.com/q/55736855
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
    os.environ["SSL_CERT_FILE"] = certifi.where()

    # validate configuration
    log_level = os.environ.get('LOG_LEVEL', 'info').upper()
    log_file = os.environ.get('LOG_FILE', None)
    log_html = utils.get_config_log_html()
    headless = utils.get_config_headless()
    server_host = os.environ.get('HOST', '0.0.0.0')
    server_port = int(os.environ.get('PORT', 8191))

    # configure logger
    logger_format = '%(asctime)s %(levelname)-8s %(message)s'
    if log_level == 'DEBUG':
        logger_format = '%(asctime)s %(levelname)-8s ReqId %(thread)s %(message)s'
    logging.basicConfig(
        format=logger_format,
        level=log_level,
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    if log_file:
        log_file = os.path.realpath(log_file)
        log_path = os.path.dirname(log_file)
        os.makedirs(log_path, exist_ok=True)

        logging.getLogger().addHandler(logging.FileHandler(log_file))

    # disable warning traces from urllib3
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.WARNING)
    logging.getLogger('undetected_chromedriver').setLevel(logging.WARNING)

    logging.info(f'FlareSolverr {utils.get_flaresolverr_version()}')
    logging.debug('Debug log enabled')

    # Get current OS for global variable
    utils.get_current_platform()

    # test browser installation
    flaresolverr_service.test_browser_installation()

    # start bootle plugins
    # plugin order is important
    app.install(logger_plugin)
    app.install(error_plugin)
    prometheus_plugin.setup()
    app.install(prometheus_plugin.prometheus_plugin)

    if env_warmup_on_boot:
        ensure_warmup()
    else:
        logging.info('Modo hibernacao: warm-up adiado ate a 1a request externa autenticada (WARMUP_ON_BOOT=false).')

    # start webserver
    # default server 'wsgiref' does not support concurrent requests
    # https://github.com/FlareSolverr/FlareSolverr/issues/680
    # https://github.com/Pylons/waitress/issues/31
    class WaitressServerPoll(ServerAdapter):
        def run(self, handler):
            from waitress import serve
            serve(handler, host=self.host, port=self.port, asyncore_use_poll=True)
    run(app, host=server_host, port=server_port, quiet=True, server=WaitressServerPoll)
