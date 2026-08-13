import { chromium } from 'playwright-core';
import path from 'node:path';

const UI = 'http://localhost:5173';
const OUT = path.resolve('prototype');
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';

const NAV = ['概览', '设定', '人物', '大纲', '正文', '素材', '导出', 'AI 讨论', '封面工坊', '图谱', '节奏'];
const WAITERS = {
  正文: '.write-textarea',
  图谱: 'svg circle',
  节奏: '.strand-card',
  'AI 讨论': '.ai-layout',
  封面工坊: 'text=生成封面',
};

const browser = await chromium.launch({ executablePath: EDGE, headless: true });
const width = Number(process.env.WIDTH || 1440);
const page = await browser.newPage({ viewport: { width, height: 900 } });
const errors = [];
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
page.on('console', (m) => {
  if (m.type() === 'error' && !m.text().includes('404')) errors.push(`console: ${m.text()}`);
});

const overflow = () =>
  page.evaluate(() => ({
    dx: document.documentElement.scrollWidth - window.innerWidth,
    dy: document.documentElement.scrollHeight - window.innerHeight,
  }));

await page.goto(UI, { waitUntil: 'networkidle' });
await page.waitForSelector('.home-hero', { timeout: 20000 });
await page.waitForTimeout(600);
const homeOv = await overflow();
await page.screenshot({ path: path.join(OUT, 'polish-home.png') });
console.log('home overflow:', JSON.stringify(homeOv));

await page.locator('.card').first().click();
await page.waitForSelector('.sidebar', { timeout: 15000 });

for (const name of NAV) {
  await page.getByRole('button', { name, exact: true }).click();
  const waiter = WAITERS[name];
  if (waiter) {
    await page.waitForSelector(waiter, { timeout: 15000 }).catch(() => undefined);
  }
  await page.waitForTimeout(700);
  const ov = await overflow();
  const fname = `polish-${name.replace(/\s/g, '')}.png`;
  await page.screenshot({ path: path.join(OUT, fname) });
  console.log(`${name}: overflow=${JSON.stringify(ov)}`);
}

console.log('errors:', errors.length ? errors : 'none');
await browser.close();
