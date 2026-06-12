const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROME = '/usr/bin/google-chrome';
const BASE = __dirname;
const DATA_FILE = path.join(BASE, '../../studio/data/carruseles_data.json');
const PNGS_DIR = path.join(BASE, 'pngs');

// Dimensiones Instagram 1:1 (1080x1080)
const W = 1080;
const H = 1080;

async function capturarCarrusel(browser, carrusel) {
  const outDir = path.join(PNGS_DIR, `${carrusel.id}-${carrusel.file}`);
  fs.mkdirSync(outDir, { recursive: true });

  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });

  // Navigate to the local server URL with capture-mode enabled
  const url = `http://localhost:3847/preview/carousel/${carrusel.id}?capture=true`;
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 20000 });

  // Wait for fonts and content to settle
  await new Promise(r => setTimeout(r, 2500));

  const slideCount = carrusel.slides.length;

  for (let i = 0; i < slideCount; i++) {
    // Switch slides in the dynamic viewer page
    await page.evaluate((slideIndex) => {
      if (window.goTo) {
        window.goTo(slideIndex);
      } else {
        // Fallback DOM manipulation if goTo is not ready
        const slides = document.querySelectorAll('.slide');
        slides.forEach((s, idx) => {
          s.style.display = idx === slideIndex ? 'flex' : 'none';
        });
      }
    }, i);

    await new Promise(r => setTimeout(r, 200));

    // Capture slide wrap (the 4:5 content area)
    const slideWrap = await page.$('.slide-wrap') || await page.$('#slideWrap');
    const filename = `slide-${String(i + 1).padStart(2, '0')}.png`;
    const filepath = path.join(outDir, filename);

    if (slideWrap) {
      await slideWrap.screenshot({ path: filepath });
    } else {
      await page.screenshot({ path: filepath, clip: { x: 30, y: 30, width: W, height: H } });
    }

    console.log(`  ✓ ${carrusel.id}-${carrusel.file}/slide-${String(i + 1).padStart(2, '0')}.png`);
  }

  await page.close();
}

(async () => {
  console.log('\n🚀 Endonautas — Generador de PNGs Dinámico');
  console.log('='.repeat(45));

  if (!fs.existsSync(DATA_FILE)) {
    console.error(`Error: No se encontró el archivo de datos en ${DATA_FILE}`);
    process.exit(1);
  }

  let carruseles = [];
  try {
    carruseles = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
  } catch (e) {
    console.error(`Error al leer base de datos JSON: ${e.message}`);
    process.exit(1);
  }

  console.log(`Cargadas ${carruseles.length} piezas desde la base de datos local.`);

  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: CHROME,
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--font-render-hinting=none',
      ],
    });

    for (const carrusel of carruseles) {
      console.log(`\n📂 ${carrusel.id} — ${carrusel.title} (${carrusel.slides.length} slides)`);
      await capturarCarrusel(browser, carrusel);
    }

    console.log('\n✅ Todos los PNGs generados en /pngs/');
    console.log('   Resolución: 1200x1500px (2x para calidad Instagram)\n');

  } catch (err) {
    console.error('Error:', err.message);
    process.exit(1);
  } finally {
    if (browser) await browser.close();
  }
})();
