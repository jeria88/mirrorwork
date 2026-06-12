const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const viewport = { width: 1080, height: 1080 };
  
  const files = [
    { input: 'propuesta-a-cine-cosmico.html', output: 'propuesta-a.jpg' },
    { input: 'propuesta-b-manuscrito-estelar.html', output: 'propuesta-b.jpg' },
    { input: 'propuesta-c-portal-interior.html', output: 'propuesta-c.jpg' },
  ];

  for (const f of files) {
    const page = await browser.newPage();
    await page.setViewportSize(viewport);
    const filePath = path.resolve('/home/nikka/Proyectos/endonautas/brand/social/propuestas-2026-05-31', f.input);
    await page.goto('file://' + filePath, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1000);
    const outputPath = path.resolve('/home/nikka/Proyectos/endonautas/brand/social/propuestas-2026-05-31', f.output);
    await page.screenshot({ path: outputPath, type: 'jpeg', quality: 95 });
    console.log('Screenshot saved:', f.output);
    await page.close();
  }

  await browser.close();
  console.log('Done');
})();
