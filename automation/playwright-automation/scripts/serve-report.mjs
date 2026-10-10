import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const repo = resolve(fileURLToPath(new URL('../../../', import.meta.url)));
const port = Number(process.env.REPORT_PORT || 4178);
const roots = {
  center: resolve(repo, 'automation/playwright-automation/report'),
  screenshots: resolve(repo, 'automation/playwright-automation/screenshots'),
  playwright: resolve(repo, 'automation/playwright-automation/playwright-report'),
  allure: resolve(repo, 'automation/playwright-automation/allure-report'),
  performance: resolve(repo, 'automation/performance-testing/k6/report-output'),
  catalog: resolve(repo, 'automation/playwright-automation/catalogs'),
  locators: resolve(repo, 'automation/playwright-automation/locators'),
  evidence: resolve(repo, 'automation/playwright-automation/evidence'),
  brand: resolve(repo, 'apps/web/public/brand'),
};
const mime = { '.html':'text/html; charset=utf-8', '.svg':'image/svg+xml', '.css':'text/css; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.json':'application/json; charset=utf-8', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.webp':'image/webp', '.webm':'video/webm', '.txt':'text/plain; charset=utf-8', '.ndjson':'application/x-ndjson', '.properties':'text/plain; charset=utf-8' };

createServer(async (request, response) => {
  let pathname;
  try { pathname = decodeURIComponent(new URL(request.url || '/', 'http://127.0.0.1').pathname); }
  catch { response.writeHead(400).end('Bad request'); return; }
  if (pathname === '/allure' || pathname === '/allure/') { response.writeHead(302, { Location:'/allure/index.html', 'Cache-Control':'no-store' }).end(); return; }
  if (pathname === '/performance' || pathname === '/performance/') { response.writeHead(302, { Location:'/performance/index.html', 'Cache-Control':'no-store' }).end(); return; }
  if (pathname === '/screenshots' || pathname === '/screenshots/') { response.writeHead(302, { Location:'/screenshots/index.html', 'Cache-Control':'no-store' }).end(); return; }
  let root = roots.center, relative = pathname === '/' ? 'index.html' : pathname.slice(1);
  for (const [prefix, name] of [['/screenshots/', 'screenshots'], ['/playwright/', 'playwright'], ['/allure/', 'allure'], ['/performance/', 'performance'], ['/brand/', 'brand'], ['/catalog/', 'catalog'], ['/locators/', 'locators'], ['/evidence/', 'evidence']]) {
    if (pathname.startsWith(prefix)) { root = roots[name]; relative = pathname.slice(prefix.length); break; }
  }
  if (pathname === '/catalog' || pathname === '/catalog/') { response.writeHead(302, { Location:'/catalog/index.html', 'Cache-Control':'no-store' }).end(); return; }
  if (pathname === '/evidence' || pathname === '/evidence/') { response.writeHead(302, { Location:'/evidence/index.html', 'Cache-Control':'no-store' }).end(); return; }
  let target = resolve(root, relative || 'index.html');
  if (target !== root && !target.startsWith(`${root}${sep}`)) { response.writeHead(403).end('Forbidden'); return; }
  try {
    if ((await stat(target)).isDirectory()) target = resolve(target, 'index.html');
    const body = request.method === 'HEAD' ? null : await readFile(target);
    response.writeHead(200, { 'Content-Type': mime[extname(target)] || 'application/octet-stream', 'Cache-Control':'no-cache', 'X-Content-Type-Options':'nosniff' });
    response.end(body);
  } catch (error) {
    const status = error?.code === 'ENOENT' || error?.code === 'ENOTDIR' ? 404 : 500;
    response.writeHead(status, { 'Content-Type':'text/plain; charset=utf-8', 'Cache-Control':'no-store' });
    response.end(status === 404 ? 'Report artifact not found. Run the matching test/report command first.' : 'Could not read report artifact.');
  }
}).listen(port, '127.0.0.1', () => console.log(`Nexora One automation report: http://127.0.0.1:${port}`));
