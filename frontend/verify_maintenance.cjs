const { chromium } = require('playwright');
const fs = require('fs');

const FRONTEND = 'http://localhost:5176';
const SHOTS = '/tmp/pdm_screenshots';
fs.mkdirSync(SHOTS, { recursive: true });

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  page.setViewportSize({ width: 1440, height: 900 });

  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', e => errors.push(e.message));

  // Step 1: load and wait for content
  console.log('Step 1: Navigate to /maintenance, wait for content');
  await page.goto(`${FRONTEND}/maintenance`);
  // Wait for either Health Matrix header or error message
  try {
    await page.waitForSelector('h3:has-text("Equipment Health Matrix"), .text-red-400', { timeout: 15000 });
    console.log('  Page fully loaded');
  } catch(e) {
    console.log('  ⚠️  Timed out waiting for content, capturing current state');
  }
  await page.screenshot({ path: `${SHOTS}/01_loaded.png` });
  const pageTitle = await page.textContent('h1').catch(() => null);
  console.log('  Page title:', pageTitle);
  console.log('  Console errors:', errors.length === 0 ? 'none' : errors.join(' | '));

  // Step 2: Health Matrix cells
  console.log('\nStep 2: Health Matrix');
  const matrixH3 = await page.textContent('h3:has-text("Equipment Health Matrix")').catch(() => null);
  console.log('  Header:', matrixH3);
  const greenCells = (await page.$$('button[title*="RUL"]')).length;
  console.log('  Equipment cells (all):', greenCells);
  const greenCount = (await page.$$('[class*="bg-green-500"][class*="w-14"]')).length;
  const yellowCount = (await page.$$('[class*="bg-yellow-400"][class*="w-14"]')).length;
  console.log(`  GREEN=${greenCount}, YELLOW=${yellowCount}`);
  const kpiTexts = await page.$$eval('.bg-slate-800 .text-xs', els => els.map(e => e.textContent?.trim()).filter(Boolean).slice(0, 6));
  console.log('  KPI labels:', kpiTexts);
  await page.screenshot({ path: `${SHOTS}/02_matrix.png` });

  // Step 3: click a cell
  console.log('\nStep 3: Equipment modal');
  const cell = await page.$('button[title*="RUL"]');
  if (cell) {
    const cellTitle = await cell.getAttribute('title');
    console.log('  Cell tooltip:', cellTitle?.replace(/\n/g, ' | '));
    await cell.click();
    await page.waitForTimeout(400);
    const modalName = await page.textContent('.fixed h3').catch(() => null);
    const modalAlert = await page.locator('.fixed').getByText(/^(GREEN|YELLOW|ORANGE|RED)$/).first().textContent().catch(() => null);
    const rulRow = await page.locator('.fixed').getByText(/RUL/).first().textContent().catch(() => null);
    console.log('  Modal: name=', modalName, '| alert=', modalAlert, '| rul row=', rulRow);
    await page.screenshot({ path: `${SHOTS}/03_modal.png` });
    const closeBtn = await page.$('button:has-text("Close")');
    if (closeBtn) await closeBtn.click();
    await page.waitForTimeout(200);
  } else {
    console.log('  ⚠️  No equipment cell found');
  }

  // Step 4: RUL Timeline
  console.log('\nStep 4: RUL Timeline');
  await page.click('button:has-text("RUL")');
  await page.waitForTimeout(600);
  const rulH3 = await page.textContent('h3:has-text("RUL Timeline")').catch(() => null);
  console.log('  Header:', rulH3);
  const bars = (await page.$$('.recharts-bar-rectangle')).length;
  const refLines = (await page.$$('.recharts-reference-line')).length;
  console.log(`  Bars: ${bars}, Reference lines: ${refLines} (expect 3)`);
  await page.screenshot({ path: `${SHOTS}/04_rul.png` });

  // Step 5: Schedule (Gantt)
  console.log('\nStep 5: Schedule (Gantt)');
  await page.click('button:has-text("Schedule")');
  await page.waitForTimeout(400);
  const ganttH3 = await page.textContent('h3:has-text("30-Day")').catch(() => null);
  console.log('  Header:', ganttH3);
  const allBlocks = (await page.$$('[class*="absolute"][class*="rounded"][class*="text-white"][class*="bg-"]:not([class*="bg-slate"])'));
  console.log('  Gantt colored blocks:', allBlocks.length);
  const summaryLine = await page.$eval('div.mt-3.text-xs', e => e.textContent).catch(() => null);
  console.log('  Summary:', summaryLine);
  await page.screenshot({ path: `${SHOTS}/05_gantt.png` });

  // Step 6: Failure History
  console.log('\nStep 6: Failure History');
  await page.click('button:has-text("Failure History")');
  await page.waitForTimeout(600);
  const trendH3 = await page.textContent('h3:has-text("Failures per Week")').catch(() => null);
  console.log('  Trend chart header:', trendH3);
  const logH3 = await page.textContent('h3:has-text("Failure Log")').catch(() => null);
  console.log('  Log header:', logH3?.slice(0, 70));
  const selects = await page.$$('select');
  console.log('  Filter selects found:', selects.length, '(expect 2)');
  const tableRows = (await page.$$('tbody tr')).length;
  console.log('  Table rows:', tableRows);
  await page.screenshot({ path: `${SHOTS}/06_history.png` });

  // Step 6b: filter
  if (selects.length > 0) {
    await selects[0].selectOption('critical');
    await page.waitForTimeout(200);
    const afterRows = (await page.$$('tbody tr')).length;
    const afterHeader = await page.textContent('h3:has-text("Failure Log")').catch(() => null);
    console.log(`  After "critical" filter: ${afterRows} rows | header: ${afterHeader?.slice(0, 60)}`);
    await page.screenshot({ path: `${SHOTS}/06b_critical_filter.png` });
    await selects[0].selectOption('');
  }

  // Step 7: Spare Parts
  console.log('\nStep 7: Spare Parts');
  await page.click('button:has-text("Spare Parts")');
  await page.waitForTimeout(400);
  const reorderBadges = (await page.$$('span.bg-red-500')).length;
  console.log('  REORDER badges (approx):', reorderBadges, '(expect 7)');
  const spareRows = (await page.$$('tbody tr')).length;
  console.log('  Spare parts rows:', spareRows);
  const abcText = await page.textContent('td span[class*="font-bold"]').catch(() => null);
  console.log('  ABC-XYZ shown:', abcText);
  await page.screenshot({ path: `${SHOTS}/07_spares.png` });

  // Step 8: switch plant
  console.log('\nStep 8: Switch to PLT-002');
  const plantSelect = await page.$('select.border-slate-700');
  if (plantSelect) {
    await plantSelect.selectOption('PLT-002');
    try {
      await page.waitForSelector('h3:has-text("Equipment Health Matrix"), h3:has-text("Spare Parts")', { timeout: 12000 });
    } catch(e) {}
    await page.waitForTimeout(1000);
    await page.click('button:has-text("Health Matrix")');
    await page.waitForTimeout(400);
    const newCells = (await page.$$('button[title*="RUL"]')).length;
    console.log('  PLT-002 equipment cells:', newCells);
    await page.screenshot({ path: `${SHOTS}/08_plt002.png` });
  }

  await browser.close();

  console.log('\n--- Summary ---');
  console.log('Console errors throughout:', errors.length === 0 ? 'none' : errors);
  console.log('Screenshots:', SHOTS);
})();
