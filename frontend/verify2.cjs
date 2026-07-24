const { chromium } = require('playwright');
const fs = require('fs');
const SHOTS = '/tmp/pdm_shots2';
fs.mkdirSync(SHOTS, { recursive: true });

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  page.setViewportSize({ width: 1440, height: 900 });

  const errors = [];
  page.on('console', msg => {
    const t = msg.type();
    if (t === 'error' || t === 'warn') errors.push(`[${t}] ${msg.text()}`);
  });

  await page.goto('http://localhost:5176/maintenance');
  // Give 15s for React + 4 API calls
  await page.waitForTimeout(8000);
  await page.screenshot({ path: `${SHOTS}/01_after8s.png`, fullPage: true });
  
  const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 500));
  console.log('Body text:', bodyText);
  console.log('Errors:', errors.slice(0, 10));
  
  await browser.close();
})();
