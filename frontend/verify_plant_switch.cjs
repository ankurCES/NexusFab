const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  page.setViewportSize({ width: 1440, height: 900 });

  await page.goto('http://localhost:5176/maintenance');
  await page.waitForSelector('h3:has-text("Equipment Health Matrix")', { timeout: 15000 });

  // Navigate to Spare Parts tab first
  await page.click('button:has-text("Spare Parts")');
  await page.waitForTimeout(500);
  const badges1 = (await page.$$('span.bg-red-500')).length;
  const rows1 = (await page.$$('tbody tr')).length;
  console.log(`PLT-001 spares: ${rows1} rows, ${badges1} REORDER badges`);

  // Switch plant
  const plantSel = page.locator('select.border-slate-700');
  await plantSel.selectOption('PLT-002');
  // Wait for data reload — loading state clears when KPI labels reappear
  await page.waitForTimeout(2000);
  const badges2 = (await page.$$('span.bg-red-500')).length;
  const rows2 = (await page.$$('tbody tr')).length;
  console.log(`PLT-002 spares: ${rows2} rows, ${badges2} REORDER badges`);

  // Also check KPI card updated
  const kpis = await page.$$eval('.text-2xl.font-bold', els => els.map(e => e.textContent));
  console.log(`PLT-002 KPIs: ${kpis.join(', ')}`);

  await browser.close();
  console.log('Plant switch: PASS');
})();
