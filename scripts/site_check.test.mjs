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
  // BLOG-017 known list: one listed broken picture + one listed dead link, and one unlisted broken picture
  knownMix: { '/': page('<img src="/old/gone.png"><a href="/post/old/">old</a><img src="/a.png">') },
  knownPlusNew: { '/': page('<img src="/old/gone.png"><img src="/new-broken.png">') },
  consoleErr: { '/': page('<img src="/a.png"><script>console.error("boom")</script>') },
  httpMix: { '/': page('<img src="/a.png"><a href="http://main.py/">main.py</a>') },
  httpOther: { '/': page('<img src="/a.png"><a href="http://main.py/">main.py</a><a href="http://other.test/x">x</a>') },
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
const KNOWN = [{ kind: 'image', path: '/old/gone.png', reason: 'r', since: '2026-11-09' },
  { kind: 'link', path: '/post/old/', reason: 'r', since: '2026-11-09' },
  { kind: 'image', path: '/a.png', reason: 'listed but works', since: '2026-11-09' }];
test('known breakage is reported, not failed; a listed path that works warns', async () => {
  const r = await check('knownMix', { known: KNOWN });
  assert.deepEqual(r.failures, []);
  assert.equal(r.ok, true);
  assert.deepEqual(r.known.map((k) => k.kind).sort(), ['image', 'link']);
  assert.deepEqual(r.warnings, ['fixed — remove from the known list: image /a.png']);
});
test('anything not on the known list still fails', async () => {
  const r = await check('knownPlusNew', { known: KNOWN });
  assert.equal(r.ok, false);
  assert.deepEqual(r.failures.filter((f) => f.kind === 'image').map((f) => new URL(f.detail).pathname), ['/new-broken.png']);
  assert.deepEqual(kinds(r), ['console', 'image']); // the unlisted 404 also logs a console error that counts
  assert.equal(r.known.length, 1);
});
test('the real list file parses: 13 entries, each with kind, path, reason, since', async () => {
  const { loadKnown } = await import('./site_check.mjs');
  const list = loadKnown(new URL('./site_check_known.json', import.meta.url).pathname);
  assert.equal(list.length, 13);
  for (const k of list) {
    assert.ok(['image', 'link', 'http'].includes(k.kind) && k.reason && k.since);
    assert.ok(k.kind === 'http' ? k.path.startsWith('http://') : k.path.startsWith('/'));
  }
});
// BLOG-017 addendum 2 (Anton round 3 F6): a console error fails by default; a limit can be given
test('one console error = failure by default', async () => {
  const r = await check('consoleErr');
  assert.equal(r.ok, false);
  assert.deepEqual(kinds(r), ['console']);
  assert.equal(r.consoleErrors, 1);
  assert.match(r.consoleSamples[0].text, /boom/);
});
test('console limit given = passes', async () => { assert.equal((await check('consoleErr', { maxConsoleErrors: 1 })).ok, true); });
test("a listed picture's own 404 console error is not counted", async () => {
  const r = await check('knownMix', { known: KNOWN });
  assert.equal(r.ok, true);
  assert.equal(r.consoleErrors, 0);
  assert.ok(r.knownConsoleErrors >= 1);
});
// D-20261109-21: http://main.py/ on the known list
const HTTP_KNOWN = [{ kind: 'http', path: 'http://main.py/', reason: 'r', since: '2026-11-09' }];
test('listed http:// target passes', async () => {
  const r = await check('httpMix', { known: HTTP_KNOWN });
  assert.equal(r.ok, true);
  assert.deepEqual(r.known.map((k) => k.detail), ['href=http://main.py/']);
});
test('unlisted http:// target still fails next to a listed one', async () => {
  const r = await check('httpOther', { known: HTTP_KNOWN });
  assert.equal(r.ok, false);
  assert.deepEqual(r.failures.map((f) => f.detail), ['href=http://other.test/x']);
});
test('a known line without a path hides nothing', async () => {
  // path missing or null: console/icon/page failures have no path either, so null === null must not match them
  const noPath = [{ kind: 'http', reason: 'r', since: '2026-11-09' }, { kind: 'console', path: null, reason: 'r', since: '2026-11-09' }];
  const http = await check('httpMix', { known: noPath });
  assert.equal(http.ok, false);
  assert.deepEqual(http.known, []);
  const consoleRun = await check('consoleErr', { known: noPath });
  assert.equal(consoleRun.ok, false);
  assert.deepEqual(kinds(consoleRun), ['console']);
});
test('pickPages: sample spreads and keeps the newest', () => {
  const entries = Array.from({ length: 30 }, (_, i) => ({ loc: `https://x/${i}`, lastmod: `2026-01-${String(i + 1).padStart(2, '0')}` }));
  const got = pickPages(entries, { sample: 5, recent: 2 });
  assert.ok(got.includes('https://x/29') && got.includes('https://x/28'));
  assert.ok(got.length <= 7 && got.length >= 5);
  assert.equal(pickPages(entries, { sample: 0, recent: 2 }).length, 30);
});
