import { spawnSync } from 'node:child_process';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { screens } from '../config/screens.js';

const root = resolve(fileURLToPath(new URL('../', import.meta.url)));
const resultsPath = resolve(root, 'report/playwright-results.json');
const reportDir = resolve(root, 'report');
const resultsDir = resolve(root, 'allure-results');
const screenshotsDir = resolve(root, 'screenshots');
await mkdir(reportDir, { recursive: true });
await mkdir(resultsDir, { recursive: true });

async function listFiles(directory, prefix = '') {
  let result = [];
  for (const entry of await readdir(directory, { withFileTypes: true }).catch(() => [])) {
    const child = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (entry.isDirectory()) result = [...result, ...(await listFiles(resolve(directory, entry.name), child))];
    else result.push(child);
  }
  return result;
}

function flatten(suites = [], parent = '') {
  const rows = [];
  for (const suite of suites) {
    const title = [parent, suite.title].filter(Boolean).join(' › ');
    for (const spec of suite.specs || []) for (const playwrightTest of spec.tests || []) {
      const result = [...(playwrightTest.results || [])].reverse().find((item) => item.status !== 'interrupted') || playwrightTest.results?.at(-1);
      rows.push({ title: spec.title, suite: title, project: playwrightTest.projectName || '', status: result?.status || 'not run', durationMs: result?.duration || 0, retry: result?.retry || 0, start: result?.startTime ? new Date(result.startTime).getTime() : 0, error: result?.error?.message || '' });
    }
    rows.push(...flatten(suite.suites || [], title));
  }
  return rows;
}

let source;
try { source = JSON.parse(await readFile(resultsPath, 'utf8')); } catch { source = null; }
let cases = flatten(source?.suites || []);
if (cases.length < 900) {
  const allureFiles = (await readdir(resultsDir).catch(() => [])).filter((file) => file.endsWith('-result.json'));
  const allureCases = [];
  for (const file of allureFiles) {
    try {
      const result = JSON.parse(await readFile(resolve(resultsDir, file), 'utf8'));
      if (result.name?.startsWith('automation evidence ·')) continue;
      const labels = Object.fromEntries((result.labels || []).map((label) => [label.name, label.value]));
      allureCases.push({ title: result.name || 'Untitled case', suite: labels.subSuite || labels.suite || 'Playwright', project: labels.parentSuite || 'Chromium', status: result.status || 'not run', durationMs: Math.max(0, (result.stop || 0) - (result.start || 0)), retry: result.retry || 0, start: result.start || 0, error: result.statusDetails?.message || '' });
    } catch { /* Ignore incomplete result files. */ }
  }
  if (allureCases.length >= cases.length) cases = allureCases;
}
const freshScreenshotFiles = await listFiles(resolve(screenshotsDir, 'runs'));
const run = {
  product: 'Nexora One', framework: 'Playwright', expectedCases: 1544,
  total: cases.length, passed: cases.filter((x) => x.status === 'passed').length,
  failed: cases.filter((x) => ['failed', 'timedOut', 'interrupted'].includes(x.status)).length,
  skipped: cases.filter((x) => x.status === 'skipped').length,
  generatedAt: new Date().toISOString(), browser: 'Chromium', cases,
  screens: screens.map((screen) => ({ ...screen, captured: freshScreenshotFiles.includes(`${screen.key}.png`) })),
};
run.notRun = Math.max(0, run.expectedCases - run.total);
await writeFile(resolve(reportDir, 'run-summary.json'), JSON.stringify(run, null, 2));

const imageFiles = await listFiles(resolve(screenshotsDir, 'product'));
const imageGallery = imageFiles.filter((file) => /\.(png|jpe?g|webp)$/i.test(file)).map((file) => `<figure><img loading="lazy" src="/screenshots/product/${file.split('/').map(encodeURIComponent).join('/')}" alt="Nexora One application screen"><figcaption>${file.split('/').map((part) => part.replace(/\.(jpe?g|png|webp)$/i, '').replaceAll('-', ' ')).join(' · ')}</figcaption></figure>`).join('');
await writeFile(resolve(screenshotsDir, 'index.html'), `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nexora One · Screen Evidence</title><style>body{margin:0;background:#f4f6fa;color:#17243b;font:13px/1.5 system-ui}header{display:flex;align-items:center;gap:22px;background:white;padding:15px 4%;border-bottom:1px solid #e5eaf2}header img{width:190px}a{color:#4169d8}.wrap{max-width:1400px;margin:auto;padding:25px 3%}h1{font-size:24px}.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:13px}figure{margin:0;background:white;border:1px solid #e5eaf2;border-radius:10px;overflow:hidden}figure img{display:block;width:100%;aspect-ratio:16/10;object-fit:cover}figcaption{padding:9px 11px;text-transform:capitalize;color:#59657a;font-size:10px}.note{color:#718096;font-size:11px}</style><header><img src="/brand/nexora-one-logo.svg" alt="Nexora One"><a href="/">Back to automation report</a></header><main class="wrap"><h1>Nexora One screen evidence</h1><p class="note">Product UI reference screenshots are separated from fresh screenshots captured by the Playwright run under <code>screenshots/runs/</code>.</p><section class="gallery">${imageGallery}</section></main></html>`);

const encoded = JSON.stringify(run).replaceAll('<', '\\u003c');
const colors = ['#4169d8','#078c78','#c16c3e','#7456b7','#1882a5','#a83f68','#678739','#e08b28','#425169','#bd4d45'];
const page = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nexora One · Automation Report</title><style>
:root{--accent:#4169d8;--ink:#17243b;--muted:#758196;--line:#e5eaf2;--surface:#fff;--canvas:#f4f6fa;--good:#168567;--bad:#bd4d55}*{box-sizing:border-box}body{margin:0;background:var(--canvas);color:var(--ink);font:13px/1.5 Inter,system-ui,sans-serif}.dark{--ink:#edf2fa;--muted:#a5b0c1;--line:#354156;--surface:#1b2638;--canvas:#101827;color-scheme:dark}.header{position:sticky;top:0;z-index:5;background:var(--surface);border-bottom:1px solid var(--line);padding:13px clamp(15px,4vw,48px);display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{width:192px;height:auto}.header-actions{display:flex;align-items:center;gap:7px}.header a,.header button{font:inherit;text-decoration:none;color:var(--ink);font-size:10px;border:1px solid var(--line);background:var(--surface);border-radius:7px;padding:8px 10px;cursor:pointer}.palette{display:flex;gap:4px}.palette button{height:17px;width:17px;border:0;border-radius:50%;padding:0}.container{max-width:1420px;margin:auto;padding:25px clamp(14px,3vw,34px) 45px}.hero{display:flex;align-items:flex-end;justify-content:space-between;gap:20px}.eyebrow{color:var(--accent);font-size:9px;letter-spacing:1.2px;font-weight:700}.hero h1{font-size:25px;letter-spacing:-.4px;margin:6px 0}.hero p{margin:0;color:var(--muted);font-size:11px}.pill{border-radius:99px;padding:6px 9px;background:#fff4d7;color:#98701c;font-size:9px;font-weight:700}.pill.ready{background:#e8f6f0;color:var(--good)}.pill.failed{background:#fff0f1;color:var(--bad)}.cards{display:grid;grid-template-columns:repeat(5,1fr);gap:11px;margin:17px 0}.card,.panel{border:1px solid var(--line);border-radius:11px;background:var(--surface);box-shadow:0 4px 16px #17243b08}.card{padding:14px}.card small{display:block;color:var(--muted);font-size:9px}.card b{display:block;font-size:22px;margin:3px 0;color:var(--accent)}.panel{padding:16px;margin-top:12px}.panel-top{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:12px}.panel h2{font-size:12px;margin:0}.panel p{color:var(--muted);font-size:10px;margin:3px 0 0}.links{display:flex;gap:7px;flex-wrap:wrap}.links a{padding:7px 9px;border-radius:7px;background:color-mix(in srgb,var(--accent) 8%,var(--surface));color:var(--accent);text-decoration:none;font-weight:600;font-size:10px}.filters{display:flex;gap:8px;margin:10px 0}.filters input,.filters select{height:33px;border:1px solid var(--line);border-radius:7px;background:var(--surface);color:var(--ink);padding:0 9px;font:inherit;font-size:10px}.filters input{flex:1}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:8px}table{width:100%;border-collapse:collapse;white-space:nowrap;font-size:10px}td,th{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-weight:600;background:var(--surface);position:sticky;top:0}.status{font-weight:700}.passed{color:var(--good)}.failed{color:var(--bad)}.not-run,.skipped{color:#9b7929}.shots{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:9px}.shots figure{margin:0;border:1px solid var(--line);border-radius:8px;overflow:hidden}.shots img{width:100%;height:130px;object-fit:cover;display:block}.shots figcaption{padding:6px 8px;font-size:9px;color:var(--muted)}.foot{color:var(--muted);font-size:9px;margin-top:18px}.theme{display:flex;gap:4px}.theme button{width:21px;height:21px;padding:0}.detail{display:none;padding:9px 11px;max-width:420px;white-space:normal;color:var(--muted)}tr.open+tr .detail{display:block}@media(max-width:850px){.cards{grid-template-columns:repeat(3,1fr)}}@media(max-width:560px){.brand{width:145px}.cards{grid-template-columns:repeat(2,1fr)}.header{align-items:flex-start}.header-actions>a{display:none}.hero{align-items:flex-start;flex-direction:column}}
</style></head><body><header class="header"><img class="brand" src="/brand/nexora-one-logo.svg" alt="Nexora One"><nav class="header-actions"><a href="/catalog/">Case catalog</a><a href="/catalog/sections/ui.html">UI</a><a href="/catalog/sections/api.html">API</a><a href="/catalog/sections/bdd.html">BDD Cucumber</a><a href="/catalog/sections/database.html">DB testing</a><a href="/evidence/">Hard case evidence</a><a href="/screenshots/index.html">Screen screenshots</a><a href="#case-rows-panel">Playwright cases</a><a href="/allure/index.html">Allure</a><a href="/performance/index.html">K6 analytics</a><a href="/performance/native-k6-report.html">Native K6</a><span class="palette">${colors.map((color) => `<button aria-label="Change header color" style="background:${color}" data-accent="${color}"></button>`).join('')}</span><button id="dark-mode" aria-label="Toggle dark theme">◐</button></nav></header><main class="container"><div class="hero"><div><div class="eyebrow">NEXORA ONE · QUALITY ENGINEERING</div><h1>Automation report center</h1><p>Playwright coverage for 42 core pages; the catalog covers 48 screens including sign-in, account lifecycle and workspace setup. It contains 400 UI, 200 API, 200 BDD Cucumber and 1,000 DB testing cases.</p></div><span id="run-pill" class="pill">Loading run status…</span></div><section class="cards" id="cards"></section><section class="panel"><div class="panel-top"><div><h2>Test suite and evidence</h2><p>Page-linked catalog, Playwright screen checks, mapped API contracts, tenant database checks and K6 workload</p></div></div><nav class="links"><a href="/catalog/sections/ui.html">Browse UI cases and types</a><a href="/catalog/sections/api.html">Browse 200 API requests</a><a href="/catalog/sections/bdd.html">Browse BDD Cucumber cases</a><a href="/catalog/sections/database.html">Browse 1,000 DB cases</a><a href="/evidence/">Add or view hard case screenshots and videos</a><a href="#case-rows-panel">Browse recorded Playwright cases</a><a href="/allure/index.html">Open Allure analytics</a><a href="/performance/index.html">Open K6 dashboard</a><a href="/screenshots/index.html">Browse screen screenshots</a></nav><p id="run-meta"></p></section><section class="panel" id="case-rows-panel"><div class="panel-top"><div><h2>Playwright test cases</h2><p id="case-count"></p></div></div><div class="filters"><input id="search" aria-label="Search automation tests" placeholder="Search case, screen or result"><select id="status-filter" aria-label="Filter by status"><option value="">All statuses</option><option>passed</option><option>failed</option><option>skipped</option><option>not run</option></select></div><div class="table-wrap"><table><thead><tr><th>Test case</th><th>Suite / screen</th><th>Browser</th><th>Duration</th><th>Status</th></tr></thead><tbody id="case-rows"></tbody></table></div></section><section class="panel"><div class="panel-top"><div><h2>Fresh run screenshots</h2><p>One full-screen capture per Nexora module, attached to the corresponding Playwright test.</p></div></div><div id="screenshots" class="shots"></div></section><p class="foot">Results are read from local Playwright/K6 outputs. Empty or unconfigured runs remain marked Not run; no results are fabricated.</p></main><script id="report-data" type="application/json">${encoded}</script><script>
const data=JSON.parse(document.querySelector('#report-data').textContent),stats={total:data.total,passed:data.passed,failed:data.failed,skipped:data.skipped,pending:data.notRun},cards=[['Playwright cases',stats.total+' / '+data.expectedCases,'actual test results recorded'],['Passed',stats.passed,'completed assertions'],['Failed',stats.failed,'failed or timed out'],['Skipped',stats.skipped,'reported by Playwright'],['Not run',stats.pending,'expected cases not yet recorded']];document.querySelector('#cards').innerHTML=cards.map(([a,b,c])=>'<article class="card"><small>'+a+'</small><b>'+b+'</b><small>'+c+'</small></article>').join('');const pill=document.querySelector('#run-pill');pill.textContent=stats.total?stats.passed+' passed · '+stats.failed+' failed · '+stats.skipped+' skipped':'No Playwright run recorded';pill.className='pill '+(stats.failed?'failed':stats.total&&stats.passed===stats.total?'ready':'');document.querySelector('#run-meta').textContent='Generated '+new Date(data.generatedAt).toLocaleString()+' · '+data.browser+' · '+data.screens.filter(x=>x.captured).length+' of '+data.screens.length+' fresh screen captures';const tbody=document.querySelector('#case-rows'),search=document.querySelector('#search'),filter=document.querySelector('#status-filter');function render(){const q=search.value.toLowerCase(),status=filter.value;const matches=data.cases.filter(x=>(!status||x.status===status)&&(!q||[x.title,x.suite,x.status,x.error].join(' ').toLowerCase().includes(q)));document.querySelector('#case-count').textContent=matches.length+' of '+data.expectedCases+' expected cases';tbody.innerHTML=matches.map((x)=>'<tr><td>'+x.title+'</td><td>'+x.suite+'</td><td>'+(x.project||'Chromium')+'</td><td>'+x.durationMs+' ms</td><td class="status '+x.status+'">'+x.status+'</td></tr>').join('')}search.oninput=filter.onchange=render;render();const gallery=document.querySelector('#screenshots');gallery.innerHTML=data.screens.map(x=>x.captured?'<figure><img loading="lazy" src="/screenshots/runs/'+x.key+'.png" alt="'+x.title+' screen screenshot"><figcaption>'+x.title+'</figcaption></figure>':'').join('')||'<p>No fresh screenshots yet. Run the Playwright suite to capture the 42 screens.</p>';document.querySelectorAll('[data-accent]').forEach(b=>b.onclick=()=>document.documentElement.style.setProperty('--accent',b.dataset.accent));document.querySelector('#dark-mode').onclick=()=>document.body.classList.toggle('dark');
</script></body></html>`;
const reportPage = page.replace(
  '<section class="cards" id="cards"></section>',
  '<section class="cards" id="cards"></section><section class="panel"><div class="panel-top"><div><h2>Case catalog coverage</h2><p>Detailed plans by suite · select a section to browse cases and filter Nexora pages.</p></div></div><div class="cards"><a class="card" href="/catalog/sections/ui.html"><small>UI cases</small><b>400</b><small>Smoke 100 · Regression 100 · Integration 100 · Negative 100</small></a><a class="card" href="/catalog/sections/api.html"><small>API cases</small><b>200</b><small>Requests, responses, tenant/auth checks and safe logs</small></a><a class="card" href="/catalog/sections/bdd.html"><small>BDD Cucumber</small><b>200</b><small>Given / When / Then in 48 feature files</small></a><a class="card" href="/catalog/sections/database.html"><small>DB testing</small><b>1,000</b><small>Tables, actions, test data, tenant context and rollback</small></a></div></section>',
);
await writeFile(resolve(reportDir, 'index.html'), reportPage);

const environment = [
  'product=Nexora One', 'testFramework=Playwright', 'browser=Chromium', 'screenCount=42',
  `expectedCases=${run.expectedCases}`, `actualCases=${run.total}`, `passed=${run.passed}`, `failed=${run.failed}`, `skipped=${run.skipped}`,
].join('\n') + '\n';
await writeFile(resolve(resultsDir, 'environment.properties'), environment);
await writeFile(resolve(resultsDir, 'executor.json'), JSON.stringify({ name: 'Nexora One local Playwright', type: 'local', buildName: `Nexora Automation · ${run.generatedAt}`, reportName: 'Nexora One Automation Report', reportUrl: 'http://127.0.0.1:4178/allure/index.html' }, null, 2));

const hasAllureResults = (await listFiles(resultsDir)).some((file) => file.endsWith('-result.json'));
const allure = resolve(root, 'node_modules/.bin', process.platform === 'win32' ? 'allure.cmd' : 'allure');
if (hasAllureResults) {
  const generated = spawnSync(allure, ['generate', './allure-results', '--clean', '-o', './allure-report'], { cwd: root, env: Object.fromEntries(Object.entries(process.env).filter(([key]) => key !== 'JAVA_HOME')), stdio: 'inherit' });
  if (generated.status !== 0) console.warn('Allure CLI did not generate a report; Playwright HTML and Nexora report center remain available.');
} else console.log('Allure report is pending a Playwright run; case output is marked Not run.');

console.log(`Nexora automation report: ${resolve(reportDir, 'index.html')}`);
