const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
    colorScheme: 'dark', // App forces dark/bg-background anyway
  });

  const outDir = path.join(__dirname, '..', 'docs', 'images', 'frontend');
  fs.mkdirSync(outDir, { recursive: true });

  console.log('Navigating to dashboard...');
  await page.goto('http://localhost:5173');
  
  // Wait for initial data and live events
  await delay(5000);
  
  console.log('Taking dashboard screenshot...');
  await page.screenshot({ path: path.join(outDir, 'dashboard.png') });

  // Violations list
  console.log('Navigating to violations...');
  await page.goto('http://localhost:5173/violations');
  await delay(2000);
  await page.screenshot({ path: path.join(outDir, 'violations.png') });

  // Get the first violation link from the table and navigate
  console.log('Navigating to violation detail...');
  try {
    const detailHref = await page.getAttribute('table a', 'href');
    if (detailHref) {
      await page.goto(`http://localhost:5173${detailHref}`);
      await delay(2000);
      await page.screenshot({ path: path.join(outDir, 'violation_detail.png') });
    }
  } catch (e) {
    console.error('Could not find violation link', e);
  }

  // Camera detail
  console.log('Navigating to camera detail...');
  await page.goto('http://localhost:5173/cameras/CAM_01');
  await delay(3000);
  await page.screenshot({ path: path.join(outDir, 'camera_detail.png') });

  // Simulate Backend Down
  console.log('Simulating Backend Down...');
  await page.route('**/api/health', route => route.abort());
  await page.goto('http://localhost:5173');
  await delay(11000); // Polling is every 10s
  await page.screenshot({ path: path.join(outDir, 'backend_down.png') });

  // Simulate WS reconnecting (since we aborted /api/health we just abort ws upgrade too or just rely on WS breaking)
  // But wait, WS reconnect is harder to simulate. Let's just create a dummy page with the banners showing by evaluating JS.
  // Not strictly necessary to use playwright for these failure states, but since they are in the docs, it's nice.
  
  await browser.close();
  console.log('Done!');
})();
