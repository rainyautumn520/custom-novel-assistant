/**
 * 端到端冒烟：驱动本机 Edge 操作真实前后端，输出截图。
 * 前置：后端 http://localhost:8000、前端 http://localhost:5173 已启动。
 * 用法：node scripts/e2e-smoke.mjs [输出目录]
 */

import { chromium } from 'playwright-core';
import { mkdirSync } from 'node:fs';
import path from 'node:path';

const API = 'http://localhost:8000';
const UI = 'http://localhost:5173';
const OUT = path.resolve(process.argv[2] ?? 'prototype');
mkdirSync(OUT, { recursive: true });

const EDGE =
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';

async function seed() {
  const res = await fetch(`${API}/api/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: '大梦山海', genre: '玄幻', target_words: 300000 }),
  });
  const project = await res.json();
  const pid = project.id;

  const post = (pathname, body) =>
    fetch(`${API}/api/projects/${pid}${pathname}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then((r) => r.json());
  const put = (pathname, body) =>
    fetch(`${API}/api/projects/${pid}${pathname}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then((r) => r.json());

  const rules = await post('/categories', { name: '规则' });
  await post('/categories', { name: '地理' });
  await post('/settings', {
    title: '灵气复苏',
    category_id: rules.id,
    content_md: '天元历 1024 年，灵气复苏开始，每十年灵气浓度翻倍。',
    tags: ['核心规则'],
    status: 'confirmed',
  });
  await post('/settings', {
    title: '天元大陆',
    content_md: '五域分立的中央大陆，北境灵脉是复苏源头。',
    tags: ['地理'],
    status: 'confirmed',
  });

  const volume = await post('/outline', {
    level: 'volume',
    title: '第一卷 · 灵起',
    goal: '主角离开灵脉村，进入天元学宫。',
  });
  const ch1 = await post('/outline', {
    level: 'chapter',
    parent_id: volume.id,
    title: '第 1 章 · 觉醒',
    target_words: 2500,
  });
  await post('/outline', {
    level: 'chapter',
    parent_id: volume.id,
    title: '第 2 章 · 入城',
    target_words: 2500,
  });
  const ch3 = await post('/outline', {
    level: 'chapter',
    parent_id: volume.id,
    title: '第 3 章 · 初入天元',
    goal: '完成学宫报到，与林晚重逢。',
    must_cover: ['报到流程', '灵气复苏背景', '林晚重逢'],
    forbidden: ['不揭示灵脉枯竭真相'],
    target_words: 2500,
    status: 'active',
  });
  await post('/outline', {
    level: 'beat',
    parent_id: ch3.id,
    title: '学宫报到',
  });
  await post('/outline', {
    level: 'beat',
    parent_id: ch3.id,
    title: '遇见林晚',
  });

  const chapter = await post(`/outline/${ch3.id}/create-chapter`, {});
  await put(`/chapters/${chapter.id}`, {
    content_md:
      '晨雾还未散尽，天元学宫的牌楼已经遥遥在望。\n\n张小凡攥紧手里的报到文书，指节微微发白。牌楼下立着一个人——墨色长发，左腕一道浅色灵纹，正是林晚。\n\n"你迟到了。"林晚说。',
  });

  const char = (body) =>
    fetch(`${API}/api/projects/${pid}/characters`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then((r) => r.json());
  const linwan = await char({
    name: '林晚',
    identity: '天元学宫内门弟子',
    personality: '外冷内热，护短',
    tags: ['女主'],
    status: 'confirmed',
  });
  await char({
    name: '张小凡',
    identity: '灵脉村少年',
    personality: '坚韧，好奇心重',
    tags: ['男主'],
  });
  const settingsList = await fetch(`${API}/api/projects/${pid}/settings`).then((r) => r.json());
  await fetch(`${API}/api/projects/${pid}/characters/${linwan.id}/links`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ settingIds: [settingsList[0].id] }),
  });
  await fetch(`${API}/api/projects/${pid}/assets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: '北境笔记', contentMd: '灵脉分布与地图灵感。', tags: ['地图'] }),
  });
  return project;
}

const browser = await chromium.launch({
  executablePath: EDGE,
  headless: true,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.on('pageerror', (e) => console.log('PAGE ERROR:', e.message));
page.on('dialog', (d) => d.accept());
page.on('console', (m) => {
  if (m.type() === 'error') console.log('CONSOLE ERROR:', m.text());
});

const project = await seed();
const pid = project.id;
await page.goto(UI, { waitUntil: 'networkidle' });
try {
  await page.waitForSelector('.card', { timeout: 15000 });
} catch (e) {
  await page.screenshot({ path: path.join(OUT, 'preview-app-debug.png') });
  console.log('URL:', page.url());
  console.log('BODY HEAD:', (await page.content()).slice(0, 800));
  throw e;
}
await page.screenshot({ path: path.join(OUT, 'preview-app-home.png') });

await page.locator('.card').first().click();
await page.waitForSelector('text=大梦山海');
await page.screenshot({ path: path.join(OUT, 'preview-app-overview.png') });

await page.getByRole('button', { name: '设定', exact: true }).click();
await page.waitForSelector('text=灵气复苏');
await page.screenshot({ path: path.join(OUT, 'preview-app-settings.png') });

await page.getByRole('button', { name: '大纲', exact: true }).click();
await page.waitForSelector('text=第一卷 · 灵起');
await page.locator('.tree-item', { hasText: '第 3 章 · 初入天元' }).click();
await page.screenshot({ path: path.join(OUT, 'preview-app-outline.png') });

await page.getByRole('button', { name: '正文', exact: true }).click();
await page.waitForSelector('.write-textarea');
await page.locator('.write-textarea').fill(
  '晨雾还未散尽，天元学宫的牌楼已经遥遥在望。\n\n张小凡抬起头，看见林晚立在牌楼下。',
);
await page.waitForSelector('text=已保存', { timeout: 10000 });
await page.screenshot({ path: path.join(OUT, 'preview-app-editor.png') });

await page.getByRole('button', { name: '生成任务书' }).click();
await page.waitForSelector('.brief-item', { timeout: 15000 });
await page.screenshot({ path: path.join(OUT, 'preview-app-editor-brief.png') });

await page.getByRole('button', { name: '五维审查' }).click();
await page.waitForSelector('.review-dim', { timeout: 15000 });
await page.screenshot({ path: path.join(OUT, 'preview-app-editor-review.png') });

await page.getByRole('button', { name: '续写', exact: true }).click();
await page.waitForSelector('.page-error', { timeout: 10000 });
await page.screenshot({ path: path.join(OUT, 'preview-app-editor-assist-503.png') });

await page.getByRole('button', { name: '人物', exact: true }).click();
await page.waitForSelector('text=林晚');
await page.locator('.char-card', { hasText: '林晚' }).click();
await page.screenshot({ path: path.join(OUT, 'preview-app-characters.png') });

await page.getByRole('button', { name: '导出', exact: true }).click();
await page.waitForSelector('.preview-item');
await page.screenshot({ path: path.join(OUT, 'preview-app-export.png') });
await page.getByRole('button', { name: '开始导出' }).click();
await page.waitForSelector('.export-summary', { timeout: 10000 });
await page.screenshot({ path: path.join(OUT, 'preview-app-export-done.png') });

await page.getByRole('button', { name: '素材', exact: true }).click();
await page.waitForSelector('text=北境笔记');
await page.screenshot({ path: path.join(OUT, 'preview-app-assets.png') });

await page.setInputFiles('input[type="file"]', {
  name: '北境灵感.txt',
  mimeType: 'text/plain',
  buffer: Buffer.from('北境地理与灵脉分布灵感记录。'),
});
await page.waitForSelector('text=北境灵感', { timeout: 10000 });
await page.screenshot({ path: path.join(OUT, 'preview-app-assets-upload.png') });

await page.getByRole('button', { name: '大纲', exact: true }).click();
await page.waitForSelector('text=第一卷 · 灵起');
const getChapterOrder = async () => {
  const items = await fetch(`${API}/api/projects/${pid}/outline`).then((r) => r.json());
  return items.filter((n) => n.level === 'chapter').map((n) => n.title);
};
const orderBefore = await getChapterOrder();
const ch1 = page.locator('.tree-item', { hasText: '第 1 章 · 觉醒' });
const ch2 = page.locator('.tree-item', { hasText: '第 2 章 · 入城' });
await ch2.dragTo(ch1, { targetPosition: { x: 5, y: 4 } });
await page.waitForTimeout(600);
const orderAfter = await getChapterOrder();
if (JSON.stringify(orderBefore) === JSON.stringify(orderAfter)) {
  throw new Error('drag did not reorder chapters');
}
console.log('drag reorder OK:', orderBefore, '->', orderAfter);

await page.getByRole('button', { name: 'AI 讨论', exact: true }).click();
await page.waitForSelector('.ai-layout');
await page.screenshot({ path: path.join(OUT, 'preview-app-ai.png') });

await page.getByRole('button', { name: '封面工坊', exact: true }).click();
await page.waitForSelector('text=生成封面');
await page.screenshot({ path: path.join(OUT, 'preview-app-covers.png') });

await page.getByRole('button', { name: '图谱', exact: true }).click();
await page.waitForSelector('svg circle', { timeout: 10000 });
await page.waitForTimeout(1200);
await page.screenshot({ path: path.join(OUT, 'preview-app-graph.png') });

console.log('E2E smoke passed, screenshots ->', OUT);
await browser.close();
