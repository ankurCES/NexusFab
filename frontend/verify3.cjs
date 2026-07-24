const { chromium } = require('playwright');
const fs = require('fs');
const SHOTS = '/tmp/pdm_shots3';
fs.mkdirSync(SHOTS, { recursive: true });

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox', '--disable-web-security'] });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  page.setViewportSize({ width: 1440, height: 900 });

  const errors = [];
  const responses = [];
  
  page.on('console', msg => errors.push(`[${msg.type()}] ${msg.text()}`));
  page.on('pageerror', e => errors.push(`[pageerror] ${e.message}: ${e.stack?.slice(0, 200)}`));
  page.on('response', r => {
    const url = r.url();
    if (url.includes('/api/') || url.includes('maintenance')) {
      responses.push(`${r.status()} ${url.slice(-50)}`);
    }
  });

  console.log('Navigating...');
  await page.goto('http://localhost:5176/maintenance', { timeout: 30000 });
  console.log('Loaded, waiting 10s...');
  await page.waitForTimeout(10000);
  
  const title = await page.$eval('h1', e => e.textContent).catch(() => 'NOT FOUND');
  const loadingDiv = await page.$eval('div.animate-pulse', e => e.textContent).catch(() => null);
  const errorDiv = await page.$eval('.text-red-400', e => e.textContent).catch(() => null);
  const bodyInner = await page.evaluate(() => document.querySelector('#root')?.innerHTML?.slice(0, 300) || 'no #root');
  
  console.log('h1:', title);
  console.log('Loading state:', loadingDiv);
  console.log('Error state:', errorDiv);
  console.log('Root HTML:', bodyInner);
  console.log('API responses:', responses);
  console.log('Errors (first 5):', errors.slice(0, 5));
  
  await page.screenshot({ path: `${SHOTS}/state.png`, fullPage: true });
  await browser.close();
  console.log('Screenshot:', `${SHOTS}/state.png`);
})();
