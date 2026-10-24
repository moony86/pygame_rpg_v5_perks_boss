// Eight-direction review using real mouse/keyboard input only.
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const args = process.argv.slice(2);
function arg(name, fallback) { const i = args.indexOf(name); return i < 0 ? fallback : args[i + 1]; }
const url = arg('--url', 'http://127.0.0.1:8766/');
const origin = new URL(url);
if (origin.hostname !== '127.0.0.1' || origin.protocol !== 'http:') throw new Error('Internal loopback only');
const modules = arg('--modules', process.env.NODE_PATH);
if (!modules) throw new Error('Pass --modules with playwright package directory');
const { chromium } = createRequire(path.join(path.resolve(modules), 'package.json'))('playwright');
const output = path.resolve(__dirname, '../../.internal-web/evidence/pistol');
fs.mkdirSync(output, { recursive: true });

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: arg('--browser', undefined) });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const observations = [];
  try {
    await page.route('https://pygame-web.github.io/**', async route => {
      const resource = new URL(route.request().url());
      const response = await page.request.get(origin.origin + '/runtime/' + resource.pathname.slice(1), { timeout: 60000 });
      await route.fulfill({ response, headers: { ...response.headers(), 'access-control-allow-origin': '*' } });
    });
    await page.route('**/*.apk', async route => {
      const response = await page.request.get(route.request().url());
      await route.fulfill({ status: 200, contentType: 'application/octet-stream', body: await response.body() });
    });
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.locator('#canvas').click({ position: { x: 10, y: 10 } });
    await page.waitForFunction(() => window.__cubeProbe?.state === 'MENU', null, { timeout: 90000 });
    await page.mouse.click(640, 353);
    await page.waitForFunction(() => window.__cubeProbe?.state === 'HUB');
    for (let angle = 0; angle < 360; angle += 45) {
      const radians = angle * Math.PI / 180;
      await page.mouse.move(640 + Math.cos(radians) * 140, 440 + Math.sin(radians) * 140);
      await page.waitForTimeout(140);
      const idle = await page.evaluate(() => window.__cubeProbe);
      if (idle.weapon !== 'pistol') throw new Error('Pistol unavailable');
      const error = Math.hypot(idle.aim[0] - Math.cos(radians), idle.aim[1] - Math.sin(radians));
      if (error > 0.03) throw new Error(`Aim mismatch ${angle}: ${error}`);
      await page.screenshot({ path: path.join(output, `idle-${angle}.png`) });
      await page.mouse.down();
      await page.waitForFunction(before => window.__cubeProbe?.shots > before, idle.shots);
      const fired = await page.evaluate(() => window.__cubeProbe);
      await page.mouse.up();
      await page.screenshot({ path: path.join(output, `shot-${angle}.png`) });
      await page.waitForTimeout(180);
      const recovered = await page.evaluate(() => window.__cubeProbe);
      if (recovered.shot_timer !== 0) throw new Error('Recoil did not recover');
      observations.push({ angle, idle, fired, recovered });
    }
    const beforeMove = await page.evaluate(() => window.__cubeProbe);
    await page.keyboard.down('d');
    await page.mouse.down();
    await page.waitForTimeout(300);
    await page.keyboard.up('d');
    await page.mouse.up();
    const afterMove = await page.evaluate(() => window.__cubeProbe);
    if (afterMove.position[0] <= beforeMove.position[0] || afterMove.shots <= beforeMove.shots) {
      throw new Error('Moving and firing together failed');
    }
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify({ observations, beforeMove, afterMove }, null, 2));
    console.log('PISTOL_BROWSER_EIGHT_DIRECTIONS_OK');
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
