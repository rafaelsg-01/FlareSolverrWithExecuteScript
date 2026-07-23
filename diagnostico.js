// diagnostico.js
// Descobre o que a rcPreloadPlayer tenta eval'ar e confirma se a correcao do
// _bigScriptString chegou na sessao. Nao lanca erro (captura tudo e retorna um relatorio).
//
// Uso: node diagnostico.js  [vid] [gid]

const ENDPOINT = process.env.FS_URL || 'http://127.0.0.1:8191/v1';
const SESSION = process.env.FS_SESSION || 'session01';
const TOKEN = process.env.TOKEN_PROXY_WEB || '';

const vid = process.argv[2] || 'APNSUSWT02EP11';
const gid = process.argv[3] || '0B265dpk7MD54MlZmTEZuaENLczQ';
const path = `/player3/server.php?categoria=vod&server=RCServer05&subfolder=ondemand&vid=${vid}&gid=${gid}`;

const JS_BODY = `
const VARS = [
  'VIDEO_URL_POST_BASE64_S0tfU0VfRlVERVVfT1RBUklPX1ZBX1BST0NVUkFSX0VNX09VVFJPX0xVR0FS',
  'VIDEO_URL_POST_BASE64_SEVfU0VfRlVERVVfT1RBUklPX1ZBX1BST0NVUkFSX0VNX09VVFJPX0xVR0FS',
  'VIDEO_URL_POST_BASE64_U0VfRlVERVVfT1RBUklPX1ZBX1BST0NVUkFSX0VNX09VVFJPX0xVR0FS',
  'VIDEO_URL_POST_BASE64_VkNfU0VfRlVERVVfT1RBUklPX1ZBX1BST0NVUkFSX0VNX09VVFJPX0xVR0FS'
];

const rel = {};
rel.bigType = typeof window._bigScriptString;
rel.bigLen = (window._bigScriptString || '').length;
rel.url_antes = location.href;

VARS.forEach(v => { delete window[v]; });
window.history.pushState(null, '', args.path);
rel.url_depois = location.href;

// intercepta TODA chamada a eval para capturar a string que quebra
window.__evals = [];
const _origEval = window.eval;
window.eval = function (c) {
  const s = String(c);
  window.__evals.push(s.length);
  try {
    return _origEval.call(window, c);
  } catch (e) {
    if (!window.__firstEvalErr) {
      window.__firstEvalErr = {
        msg: String((e && (e.message || e)) || e),
        len: s.length,
        head: s.slice(0, 500),
        tail: s.slice(-200)
      };
    }
    throw e;
  }
};

// 1) roda o _bigScriptString (define rcPreloadPlayer)
try {
  (0, eval)(window._bigScriptString);
  rel.bootOk = true;
} catch (e) {
  rel.bootOk = false;
  rel.bootErr = String((e && (e.stack || e)) || e).slice(0, 400);
}

rel.rcPreloadPlayerType = typeof window.rcPreloadPlayer;

// 2) chama rcPreloadPlayer e captura o erro interno
if (rel.bootOk && typeof window.rcPreloadPlayer === 'function') {
  try {
    window.rcPreloadPlayer(Date.now());
    rel.preloadOk = true;
  } catch (e) {
    rel.preloadOk = false;
    rel.preloadErr = String((e && (e.message || e)) || e).slice(0, 300);
  }
}

rel.numEvals = window.__evals.length;
rel.evalLens = window.__evals.slice(0, 25);
rel.firstEvalErr = window.__firstEvalErr || null;

return rel;
`;

(async () => {
  const url = TOKEN ? `${ENDPOINT}?token=${encodeURIComponent(TOKEN)}` : ENDPOINT;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      cmd: 'request.get',
      session: SESSION,
      maxTimeout: 120000,
      directJs: JS_BODY,
      directJsArgs: { path }
    })
  });
  const data = await res.json();
  if (data.status !== 'ok') {
    console.error('directJs falhou (nao deveria, ele captura tudo):', data.message);
    process.exit(1);
  }
  const rel = JSON.parse(data.solution.response);
  console.log(JSON.stringify(rel, null, 2));

  console.log('\n--- leitura rapida ---');
  console.log('_bigScriptString len :', rel.bigLen, rel.bigLen === 132655 ? '(OK, correcao chegou)' : '(ESPERADO 132655 - correcao NAO chegou na sessao!)');
  console.log('rcPreloadPlayer      :', rel.rcPreloadPlayerType);
  if (rel.firstEvalErr) {
    console.log('\n>>> eval que QUEBROU:');
    console.log('    msg :', rel.firstEvalErr.msg);
    console.log('    len :', rel.firstEvalErr.len);
    console.log('    head:', rel.firstEvalErr.head);
    console.log('    tail:', rel.firstEvalErr.tail);
  } else {
    console.log('\nnenhum eval quebrou - preloadOk =', rel.preloadOk);
  }
})().catch((e) => { console.error('ERRO:', e.message); process.exit(1); });
