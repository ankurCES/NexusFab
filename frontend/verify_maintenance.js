const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const FRONTEND = 'http://localhost:5176';
const SCREENSHOTS = '/tmp/pdm_screenshots';
fs.mkdirSync(SCREENSHOTS, { recursive: true });

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  page.setViewportSize({ width: 1440, height: 900 });

  // --- Step 1: Load page ---
  console.log('Step 1: Navigate to /maintenance');
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  await page.goto(`${FRONTEND}/maintenance`, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${SCREENSHOTS}/01_loaded.png` });
  console.log('  Console errors:', errors.length === 0 ? 'none' : errors);

  // --- Step 2: Health Matrix tab (default) ---
  console.log('\nStep 2: Health Matrix tab (default)');
  const matrixTitle = await page.textContent('h3:has-text("Equipment Health Matrix")').catch(() => null);
  console.log('  Health Matrix header found:', !!matrixTitle);
  
  // Count equipment cells by alert level
  const greenCells = await page.$$('.bg-green-500[class*="w-14"]');
  const yellowCells = await page.$$('.bg-yellow-400[class*="w-14"]');
  const orangeCells = await page.$$('.bg-orange-500[class*="w-14"]');
  const redCells = await page.$$('.bg-red-600[class*="w-14"]');
  console.log(`  Cells: GREEN=${greenCells.length}, YELLOW=${yellowCells.length}, ORANGE=${orangeCells.length}, RED=${redCells.length}`);
  await page.screenshot({ path: `${SCREENSHOTS}/02_health_matrix.png` });

  // --- Step 3: Click a cell to open modal ---
  console.log('\nStep 3: Click equipment cell for modal');
  const firstCell = await page.$('button[title*="RUL"]');
  if (firstCell) {
    const title = await firstCell.getAttribute('title');
    console.log('  Cell title:', title?.slice(0, 80));
    await firstCell.click();
    await page.waitForTimeout(300);
    const modalEquip = await page.textContent('.fixed .bg-slate-800 h3').catch(() => null);
    console.log('  Modal equipment name:', modalEquip);
    const rulText = await page.locator('.fixed .bg-slate-800').getByText(/RUL/).first().textContent().catch(() => null);
    console.log('  Modal RUL row:', rulText);
    await page.screenshot({ path: `${SCREENSHOTS}/03_modal.png` });
    await page.keyboard.press('Escape');
    const closeBtn = await page.$('.fixed button:has-text("Close")');
    if (closeBtn) await closeBtn.click();
    await page.waitForTimeout(200);
  } else {
    console.log('  ⚠️  No cell found with RUL title');
  }

  // --- Step 4: RUL Timeline tab ---
  console.log('\nStep 4: RUL Timeline tab');
  await page.click('button:has-text("RUL Timeline")');
  await page.waitForTimeout(500);
  const rulTitle = await page.textContent('h3:has-text("RUL Timeline")').catch(() => null);
  console.log('  RUL Timeline header found:', !!rulTitle);
  // Check for recharts bars
  const bars = await page.$$('.recharts-bar-rectangle');
  console.log('  Recharts bars found:', bars.length);
  // Check for reference lines (threshold markers)
  const refLines = await page.$$('.recharts-reference-line');
  console.log('  Reference lines found:', refLines.length, '(expected 3)');
  await page.screenshot({ path: `${SCREENSHOTS}/04_rul_timeline.png` });

  // --- Step 5: Schedule / Gantt tab ---
  console.log('\nStep 5: Schedule (Gantt) tab');
  await page.click('button:has-text("Schedule")');
  await page.waitForTimeout(300);
  const ganttTitle = await page.textContent('h3:has-text("30-Day Maintenance Calendar")').catch(() => null);
  console.log('  Gantt header found:', !!ganttTitle);
  const dayLabels = await page.$$('span:has-text("+0d")');
  console.log('  Day label (+0d) found:', dayLabels.length > 0);
  const blocks = await page.$$('.bg-blue-500, .bg-orange-400, .bg-red-500');
  console.log('  Gantt blocks (blue/orange/red):', blocks.length);
  const ganttSummary = await page.textContent('div.mt-3.text-xs').catch(() => null);
  console.log('  Gantt summary line:', ganttSummary);
  await page.screenshot({ path: `${SCREENSHOTS}/05_gantt.png` });

  // --- Step 6: Failure History tab ---
  console.log('\nStep 6: Failure History tab');
  await page.click('button:has-text("Failure History")');
  await page.waitForTimeout(500);
  const histTitle = await page.textContent('h3:has-text("Failures per Week")').catch(() => null);
  console.log('  Trend chart header:', !!histTitle);
  const logHeader = await page.textContent('h3:has-text("Failure Log")').catch(() => null);
  console.log('  Failure Log header:', logHeader?.slice(0, 60));
  const severitySelect = await page.$('select');
  console.log('  Severity filter select found:', !!severitySelect);
  const tableRows = await page.$$('tbody tr');
  console.log('  Table rows:', tableRows.length);
  await page.screenshot({ path: `${SCREENSHOTS}/06_history.png` });

  // Step 6a: Test severity filter
  console.log('  Testing severity filter (critical)...');
  const selects = await page.$$('select');
  if (selects.length > 0) {
    await selects[0].selectOption('critical');
    await page.waitForTimeout(200);
    const critRows = await page.$$('tbody tr');
    const critLogHeader = await page.textContent('h3:has-text("Failure Log")').catch(() => null);
    console.log('  After filter: rows =', critRows.length, '| header:', critLogHeader?.slice(0, 60));
    await selects[0].selectOption('');
  }
  await page.screenshot({ path: `${SCREENSHOTS}/06b_filtered.png` });

  // --- Step 7: Spare Parts tab ---
  console.log('\nStep 7: Spare Parts tab');
  await page.click('button:has-text("Spare Parts")');
  await page.waitForTimeout(300);
  const reorderBadges = await page.$$('span.bg-red-500:has-text("REORDER")');
  console.log('  REORDER badges found:', reorderBadges.length, '(expected 7)');
  const sparesRows = await page.$$('tbody tr');
  console.log('  Spare parts rows:', sparesRows.length);
  const abcXyz = await page.textContent('td:has-text("AY")').catch(() => null);
  console.log('  ABC-XYZ classification shown:', !!abcXyz);
  await page.screenshot({ path: `${SCREENSHOTS}/07_spares.png` });

  // --- Step 8: Plant switcher ---
  console.log('\nStep 8: Plant switcher (PLT-001 → PLT-002)');
  const select = await page.$('select.bg-slate-800');
  if (select) {
    await select.selectOption('PLT-002');
    await page.waitForTimeout(2000); // wait for re-fetch
    const reorderBadges2 = await page.$$('span.bg-red-500:has-text("REORDER")');
    console.log('  PLT-002 REORDER badges:', reorderBadges2.length);
    await page.screenshot({ path: `${SCREENSHOTS}/08_plt002.png` });
  }

  await browser.close();
  console.log('\n✅ All screenshots saved to', SCREENSHOTS);
})();
