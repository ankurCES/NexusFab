const { chromium } = require('playwright');
const fs = require('fs');
const SHOTS = '/tmp/pdm_final';
fs.mkdirSync(SHOTS, { recursive: true });

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  page.setViewportSize({ width: 1440, height: 900 });

  await page.goto('http://localhost:5176/maintenance');
  await page.waitForSelector('h3:has-text("Equipment Health Matrix")', { timeout: 15000 });

  // 1. Health Matrix
  await page.screenshot({ path: `${SHOTS}/1_health_matrix.png` });
  const cells = await page.$$('button[title*="RUL"]');
  console.log(`Health Matrix: ${cells.length} equipment cells`);

  // 2. Modal
  await cells[1].click(); // click FILLER (YELLOW) cell
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${SHOTS}/2_modal.png` });
  const modalName = await page.$eval('.fixed h3', e => e.textContent).catch(() => null);
  const rulLine = await page.locator('.fixed').getByText('RUL').first().textContent().catch(() => null);
  console.log(`Modal: name="${modalName}", RUL row="${rulLine}"`);
  await page.click('button:has-text("Close")');

  // 3. RUL Timeline
  await page.click('button:has-text("RUL")');
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${SHOTS}/3_rul_timeline.png` });
  const bars = (await page.$$('.recharts-bar-rectangle')).length;
  const refs = (await page.$$('.recharts-reference-line')).length;
  console.log(`RUL Timeline: ${bars} bars, ${refs} reference lines`);

  // 4. Schedule
  await page.click('button:has-text("Schedule")');
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${SHOTS}/4_gantt.png` });
  const summary = await page.$eval('div.mt-3', e => e.textContent).catch(() => null);
  console.log(`Gantt: ${summary}`);

  // 5. Failure History
  await page.click('button:has-text("Failure History")');
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${SHOTS}/5_history.png` });
  const logH = await page.$eval('h3:has-text("Failure Log")', e => e.textContent);
  console.log(`History: ${logH}`);

  // filter using label-based selector
  const sevSelect = await page.locator('select').nth(1); // 0=plant, 1=severity
  await sevSelect.selectOption({ value: 'critical' });
  await page.waitForTimeout(200);
  const critH = await page.$eval('h3:has-text("Failure Log")', e => e.textContent);
  console.log(`After critical filter: ${critH}`);
  await page.screenshot({ path: `${SHOTS}/5b_critical.png` });
  await sevSelect.selectOption({ value: '' });

  // 6. Spare Parts
  await page.click('button:has-text("Spare Parts")');
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${SHOTS}/6_spares.png` });
  const badges = (await page.$$('span.bg-red-500')).length;
  const spareRows = (await page.$$('tbody tr')).length;
  const days14 = (await page.$$('[class*="text-red-400"]')).length;
  console.log(`Spares: ${spareRows} parts, ${badges} REORDER badges, ${days14} red-highlight cells`);

  // 7. Plant switch
  const plantSel = page.locator('select.border-slate-700');
  await plantSel.selectOption('PLT-002');
  await page.waitForSelector('h3:has-text("Spare Parts")', { timeout: 15000 });
  await page.waitForTimeout(500);
  const badges2 = (await page.$$('span.bg-red-500')).length;
  console.log(`PLT-002 REORDER badges: ${badges2}`);
  await page.screenshot({ path: `${SHOTS}/7_plt002.png` });

  await browser.close();
  console.log('\nAll screenshots:', SHOTS);
})();
