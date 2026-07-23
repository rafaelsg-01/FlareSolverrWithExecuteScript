// testar-player.js
// Manda a sequencia do player (delete vars -> pushState -> eval -> rcPreloadPlayer -> loop)
// para a aba do FlareSolverr via directJs e imprime as VIDEO_URL_POST_BASE64_ encontradas.
//
// Requer o servidor no ar (run-local.ps1 ou docker) e a aba ja aquecida.
//
// Uso:
//   node testar-player.js
//   node testar-player.js APNSUSWT02EP09 0B265dpk7MD54N3V2NnVCZVF1X2s
//
// Env opcionais: FS_URL, FS_SESSION, TOKEN_PROXY_WEB

const ENDPOINT = process.env.FS_URL || 'http://127.0.0.1:8191/v1';
const SESSION = process.env.FS_SESSION || 'session01';
const TOKEN = process.env.TOKEN_PROXY_WEB || '';

const vid = process.argv[2] || 'APNSUSWT02EP11';
const gid = process.argv[3] || '0B265dpk7MD54MlZmTEZuaENLczQ';
const path = `/player3/server.php?categoria=vod&server=RCServer05&subfolder=ondemand&vid=APNSUSWT02EP15&gid=0B265dpk7MD54aVNnaXFYeUNvZ3c`;

// Este corpo e exatamente o mesmo que voce cola no console do navegador
// (la ele vai dentro de um (async () => { ... })(); aqui vai cru, o directJs embrulha).
const JS_BODY = `
const VARS = [
  'VIDEO_URL_POST_BASE64_S0tfU0VfRlVERVVfT1RBUklPX1ZBX1BST0NVUkFSX0VNX09VVFJPX0xVR0FS',
  'VIDEO_URL_POST_BASE64_SEVfU0VfRlVERVVfT1RBUklPX1ZBX1BST0NVUkFSX0VNX09VVFJPX0xVR0FS',
  'VIDEO_URL_POST_BASE64_U0VfRlVERVVfT1RBUklPX1ZBX1BST0NVUkFSX0VNX09VVFJPX0xVR0FS',
  'VIDEO_URL_POST_BASE64_VkNfU0VfRlVERVVfT1RBUklPX1ZBX1BST0NVUkFSX0VNX09VVFJPX0xVR0FS'
];

const PATH = '${path}';

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

VARS.forEach(v => { delete window[v]; });

window.history.pushState(null, '', PATH);

(0, eval)(window._bigScriptString);

window.rcPreloadPlayer(Date.now());

await sleep(1000);

const LIMITE = Date.now() + 60000;
let encontrados = [];
while (Date.now() < LIMITE) {
  encontrados = VARS.map(v => window[v]).filter(v => typeof v === 'string' && v.length > 5);
  if (encontrados.length >= 1) break;
  await sleep(200);
}

if (!encontrados.length) throw new Error('timeout: nenhuma VIDEO_URL_POST_BASE64_ preenchida em 60s');
return encontrados;
`;

(async () => {
  const url = TOKEN ? `${ENDPOINT}?token=${encodeURIComponent(TOKEN)}` : ENDPOINT;
  console.log('vid  :', vid);
  console.log('path :', path);

  const t0 = Date.now();
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      cmd: 'request.get',
      session: SESSION,
      maxTimeout: 180000,
      directJs: JS_BODY,
      directJsArgs: { path }
    })
  });

  const data = await res.json();
  console.log('data :', JSON.parse(data.solution.response));
  const secs = ((Date.now() - t0) / 1000).toFixed(1);

  if (data.status !== 'ok') {
    console.error(`\nFALHOU (${secs}s):`, data.message);
    process.exit(1);
  }

  const urls = JSON.parse(data.solution.response);
  console.log(`\nOK (${secs}s) - ${urls.length} url(s):`);
  urls.forEach((u, i) => console.log(`  [${i}] ${u}`));
})().catch((e) => {
  console.error('ERRO:', e.message);
  process.exit(1);
});
