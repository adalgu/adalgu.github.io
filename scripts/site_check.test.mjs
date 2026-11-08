// Local, no external network: serves a tiny static site from memory and runs the real browser check.
// PLAYWRIGHT_MODULE=<path to playwright> may point at an existing install.
import test, { after, before } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { siteCheck, pickPages } from './site_check.mjs';

// 1x1 PNG
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
const page = (body) => `<!doctype html><html><head><meta charset=utf-8><title>t</title><link rel="icon" href="/favicon.ico"><link rel="apple-touch-icon" href="/apple-touch-icon.png"></head><body>${body}</body></html>`;
const sitemap = (paths) => `<?xml version="1.0"?><urlset>${paths.map((p, i) => `<url><loc>https://example.test${p}</loc><lastmod>2026-11-0${(i % 9) + 1}</lastmod></url>`).join('')}</urlset>`;

const SITES = {
  good: { '/': page('<img src="/a.png"><a href="/p/">p</a>'), '/p/': page('<img src="/a.png"><a href="/">home</a>') },
  badImage: { '/': page('<img src="/missing.png">') },
  httpLink: { '/': page('<a href="http://example.test/x">x</a>') },
  deadLink: { '/': page('<a href="/nope/">dead</a>') },
  noIcon: { '/': page('<img src="/a.png">') },
};
const servers = {};
const serve = (name, pages) => new Promise((ok) => {
  const s = http.createServer((req, res) => {
    const p = req.url.split('?')[0];
    if (p === '/sitemap.xml') { res.setHeader('content-type', 'application/xml'); return res.end(sitemap(Object.keys(pages))); }
    if (pages[p]) { res.setHeader('content-type', 'text/html'); return res.end(pages[p]); }
    if (p === '/a.png') { res.setHeader('content-type', 'image/png'); return res.end(PNG); }
    if (name !== 'noIcon' && (p === '/favicon.ico' || p === '/apple-touch-icon.png')) { res.setHeader('content-type', 'image/png'); return res.end(PNG); }
    res.statusCode = 404; res.end('nope');
  }).listen(0, '127.0.0.1', () => ok(s));
});
before(async () => { for (const [n, p] of Object.entries(SITES)) servers[n] = await serve(n, p); });
after(() => Object.values(servers).forEach((s) => s.close()));
const check = (name, extra = {}) => siteCheck({ base: `http://127.0.0.1:${servers[name].address().port}`, ...extra });
const kinds = (r) => [...new Set(r.failures.map((f) => f.kind))].sort();

test('clean site passes, all sitemap pages visited', async () => {
  const r = await check('good');
  assert.deepEqual(r.failures, []);
  assert.equal(r.ok, true);
  assert.equal(r.pages, 2);
});
test('404 image -> image failure', async () => { const r = await check('badImage'); assert.equal(r.ok, false); assert.ok(kinds(r).includes('image')); });
test('http:// link -> http failure', async () => { const r = await check('httpLink'); assert.equal(r.ok, false); assert.ok(kinds(r).includes('http')); });
test('dead internal link -> link failure', async () => { const r = await check('deadLink'); assert.equal(r.ok, false); assert.ok(kinds(r).includes('link')); });
test('missing icons -> icon failure', async () => { const r = await check('noIcon'); assert.equal(r.ok, false); assert.ok(kinds(r).includes('icon')); });
test('pickPages: sample spreads and keeps the newest', () => {
  const entries = Array.from({ length: 30 }, (_, i) => ({ loc: `https://x/${i}`, lastmod: `2026-01-${String(i + 1).padStart(2, '0')}` }));
  const got = pickPages(entries, { sample: 5, recent: 2 });
  assert.ok(got.includes('https://x/29') && got.includes('https://x/28'));
  assert.ok(got.length <= 7 && got.length >= 5);
  assert.equal(pickPages(entries, { sample: 0, recent: 2 }).length, 30);
});
