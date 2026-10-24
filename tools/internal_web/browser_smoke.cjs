// Private QA only: ordinary browser mouse/keyboard input, read-only telemetry.
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');

const args = process.argv.slice(2);
function arg(name, fallback) {
  const index = args.indexOf(name);
  return index < 0 ? fallback : args[index + 1];
}
const url = arg('--url', 'http://127.0.0.1:8766/');
const parsed = new URL(url);
if (parsed.hostname !== '127.0.0.1' || parsed.protocol !== 'http:') {
  throw new Error('Only the loopback internal QA server is allowed');
}
const modules = arg('--modules', process.env.NODE_PATH);
if (!modules) throw new Error('Pass --modules with the directory containing playwright');
const { chromium } = createRequire(path.join(path.resolve(modules), 'package.json'))('playwright');
const output = path.resolve(__dirname, '../../.internal-web/evidence');
fs.mkdirSync(output, { recursive: true });

async function run() {
  const browser = await chromium.launch({ headless: true, executablePath: arg('--browser', undefined) });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const observations = [];
  const probe = () => page.evaluate(() => window.__cubeProbe);
  const record = async label => observations.push({ label, ...await probe() });
  try {
    // The isolated QA browser cannot fetch the official CDN directly. Replay
    // the same bytes from the allowlisted local runtime cache, with CORS.
    await page.route('https://pygame-web.github.io/**', async route => {
      const resource = new URL(route.request().url());
      const response = await page.request.get(parsed.origin + '/runtime/' + resource.pathname.slice(1), { timeout: 60000 });
      await route.fulfill({ response, headers: { ...response.headers(), 'access-control-allow-origin': '*' } });
    });
    // Streaming package requests in this environment returned empty responses;
    // replay the complete local package through the supported route API.
    await page.route('**/*.apk', async route => {
      const response = await page.request.get(route.request().url());
      if (!response.ok()) throw new Error('Package transfer failed');
      await route.fulfill({ status: 200, contentType: 'application/octet-stream', body: await response.body() });
    });
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    // Satisfy browser audio engagement, without injecting gameplay state.
    await page.locator('#canvas').click({ position: { x: 10, y: 10 } });
    await page.waitForFunction(() => window.__cubeProbe?.state === 'MENU', null, { timeout: 90000 });
    await record('menu');
    await page.mouse.click(640, 353);
    await page.waitForFunction(() => window.__cubeProbe?.state === 'HUB');
    await record('new_run_hub');
    const baseline = await probe();
    await page.keyboard.down('w');
    await page.waitForFunction(() => window.__cubeProbe?.position[1] <= 440, null, { timeout: 3000 });
    await page.keyboard.up('w');
    if ((await probe()).position[1] >= baseline.position[1]) throw new Error('Movement did not reach Python');
    await record('moved_to_gatekeeper');
    await page.keyboard.press('e');
    await page.waitForTimeout(150);
    await page.keyboard.press('e');
    await page.waitForFunction(() => window.__cubeProbe?.state === 'ROOM');
    await record('entered_room');
    await page.keyboard.down('d');
    await page.keyboard.press('Space', { delay: 50 });
    await page.waitForFunction(() => window.__cubeProbe?.dashes >= 1);
    await page.keyboard.up('d');
    await record('dash');
    const shotsBefore = (await probe()).shots;
    await page.mouse.move(640, 90);
    await page.mouse.down();
    await page.waitForFunction(before => window.__cubeProbe?.shots >= before + 2, shotsBefore);
    await page.mouse.up();
    await page.waitForFunction(() => window.__cubeProbe?.enemies > 0);
    await record('firing_with_enemies');
    await page.screenshot({ path: path.join(output, 'smoke-combat.png') });
    await page.keyboard.press('Escape');
    await page.waitForFunction(() => window.__cubeProbe?.state === 'PAUSED');
    await record('paused');
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => window.__cubeProbe?.state === 'MENU');
    await record('returned_to_menu');
    fs.writeFileSync(path.join(output, 'smoke-results.json'), JSON.stringify({ internal_test_only: true, observations }, null, 2));
    console.log('INTERNAL_BROWSER_SMOKE_OK');
    console.log(JSON.stringify(observations, null, 2));
  } finally {
    await browser.close();
  }
}

run().catch(error => { console.error(error); process.exitCode = 1; });
