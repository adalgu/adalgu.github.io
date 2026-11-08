#!/usr/bin/env node
// Browser check of a built site (local static server or production).
//   node scripts/site_check.mjs --base http://127.0.0.1:4173 [--sample 20] [--recent 5] [--max-console-errors N] [--out result.json]
// Pages: home + sitemap.xml entries (all when --sample is omitted; otherwise N evenly spread + the --recent newest).
// Per page: every <img> naturalWidth > 0 · no http:// in any href/src (own-origin http is allowed only when the checked base itself is http, i.e. a local server) · internal links answer < 400 · icons answer 200.
// Console errors are counted and reported; they fail the run only with --max-console-errors.
// Prints JSON, exit 1 when there is any failure.
import { createRequire } from 'node:module';
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);

export const pickPages = (entries, { sample, recent }) => {
  if (!sample || entries.length <= sample + recent) return entries.map((e) => e.loc);
  const newest = [...entries].sort((a, b) => (b.lastmod || '').localeCompare(a.lastmod || '')).slice(0, recent);
  const rest = entries.filter((e) => !newest.includes(e));
  const step = rest.length / sample;
  const spread = Array.from({ length: sample }, (_, i) => rest[Math.floor(i * step)]);
  return [...new Set([...newest, ...spread].map((e) => e.loc))];
};

const parseSitemap = (xml) =>
  [...xml.matchAll(/<url>([\s\S]*?)<\/url>/g)].map((m) => ({
    loc: /<loc>\s*([^<\s]+)\s*<\/loc>/.exec(m[1])?.[1],
    lastmod: /<lastmod>\s*([^<\s]+)\s*<\/lastmod>/.exec(m[1])?.[1],
  })).filter((e) => e.loc);

export async function siteCheck({ base, sample = 0, recent = 5, maxConsoleErrors = Infinity, playwright }) {
  const { chromium } = playwright ?? require(process.env.PLAYWRIGHT_MODULE || 'playwright');
  const origin = new URL(base).origin;
  const failures = [];
  const fail = (page, kind, detail) => failures.push({ page, kind, detail });
  const browser = await chromium.launch({ headless: true });
  try {
    const ctx = await browser.newContext();
    const api = ctx.request;
    const status = async (url) => { try { return (await api.get(url, { maxRedirects: 5, timeout: 15000 })).status(); } catch (e) { return `error: ${String(e).slice(0, 80)}`; } };
    const seen = new Map();
    const statusOnce = (url) => { if (!seen.has(url)) seen.set(url, status(url)); return seen.get(url); };

    // sitemap entries carry the production host; check the same paths on `base`
    let paths = ['/'];
    const sm = await api.get(`${origin}/sitemap.xml`).catch(() => null);
    if (sm?.ok()) {
      const entries = parseSitemap(await sm.text()).map((e) => ({ ...e, loc: new URL(new URL(e.loc).pathname, origin).href }));
      paths = [...new Set([`${origin}/`, ...pickPages(entries, { sample, recent })])];
    } else {
      fail('/sitemap.xml', 'sitemap', `status ${sm ? sm.status() : 'unreachable'}; checking home only`);
      paths = [`${origin}/`];
    }

    let consoleErrors = 0;
    const iconUrls = new Set([`${origin}/favicon.ico`]);
    for (const url of paths) {
      const page = await ctx.newPage();
      page.on('console', (m) => { if (m.type() === 'error') consoleErrors++; });
      page.on('pageerror', () => { consoleErrors++; });
      const res = await page.goto(url, { waitUntil: 'load', timeout: 30000 }).catch((e) => ({ err: String(e).slice(0, 100) }));
      if (!res || res.err || res.status() >= 400) { fail(url, 'page', res?.err ?? `status ${res?.status()}`); await page.close(); continue; }
      await page.evaluate(() => document.querySelectorAll('img[loading=lazy]').forEach((i) => { i.loading = 'eager'; }));
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
      const dom = await page.evaluate((localHttp) => {
        const abs = (v) => { try { return new URL(v, document.baseURI).href; } catch { return null; } };
        return {
          broken: [...document.images].filter((i) => !(i.naturalWidth > 0)).map((i) => i.currentSrc || i.getAttribute('src') || '(no src)'),
          http: [...document.querySelectorAll('[href],[src]')].flatMap((e) => ['href', 'src'].map((a) => [a, e.getAttribute(a)])).filter(([, v]) => v && /^http:\/\//i.test(v) && !(localHttp && new URL(v).origin === location.origin)).map(([a, v]) => `${a}=${v}`),
          links: [...document.querySelectorAll('a[href]')].map((a) => abs(a.getAttribute('href'))).filter(Boolean),
          icons: [...document.querySelectorAll('link[rel~=icon],link[rel=apple-touch-icon],link[rel=mask-icon]')].map((l) => abs(l.getAttribute('href'))).filter(Boolean),
        };
      }, origin.startsWith('http:'));
      for (const s of dom.broken) fail(url, 'image', s);
      for (const s of dom.http) fail(url, 'http', s);
      for (const l of new Set(dom.links)) {
        const u = new URL(l);
        if (u.origin !== origin || !/^https?:$/.test(u.protocol)) continue;
        u.hash = '';
        const st = await statusOnce(u.href);
        if (typeof st !== 'number' || st >= 400) fail(url, 'link', `${u.pathname} -> ${st}`);
      }
      dom.icons.forEach((i) => iconUrls.add(i));
      await page.close();
    }
    for (const icon of iconUrls) {
      if (new URL(icon).origin !== origin) continue;
      const st = await statusOnce(icon);
      if (st !== 200) fail(icon, 'icon', `status ${st}`);
    }
    if (consoleErrors > maxConsoleErrors) fail('(all pages)', 'console', `${consoleErrors} console errors > ${maxConsoleErrors}`);
    return { base: origin, pages: paths.length, consoleErrors, failures, ok: failures.length === 0 };
  } finally {
    await browser.close();
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const arg = (name, dflt) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : dflt; };
  const result = await siteCheck({
    base: arg('base', 'http://127.0.0.1:4173'),
    sample: Number(arg('sample', 0)),
    recent: Number(arg('recent', 5)),
    maxConsoleErrors: arg('max-console-errors') === undefined ? Infinity : Number(arg('max-console-errors')),
  });
  const out = JSON.stringify(result, null, 2);
  if (arg('out')) writeFileSync(arg('out'), out + '\n');
  console.log(out);
  process.exit(result.ok ? 0 : 1);
}
