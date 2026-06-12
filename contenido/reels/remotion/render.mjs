import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import { createRequire } from 'module';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const ffmpegPath = require('ffmpeg-static');

const outDir = path.join(__dirname, '..', 'mp4');
fs.mkdirSync(outDir, { recursive: true });

const DATA_FILE = path.join(__dirname, 'src', 'reels_data.json');

async function main() {
  console.log('\n🎬 Endonautas — Generador de Reels Faceless Dinámico');
  console.log('='.repeat(50));

  if (!fs.existsSync(DATA_FILE)) {
    console.error(`Error: No se encontró reels_data.json en ${DATA_FILE}`);
    process.exit(1);
  }

  let reelsData = [];
  try {
    reelsData = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
  } catch (e) {
    console.error(`Error al leer reels_data.json: ${e.message}`);
    process.exit(1);
  }

  const compositions = reelsData.map(r => ({ id: r.id, label: `${r.title} (${r.duration}s)` }));

  console.log('📦 Bundling componentes React...\n');

  const bundleLocation = await bundle({
    entryPoint: path.resolve(__dirname, 'src/index.jsx'),
    webpackOverride: (config) => config,
    enableCaching: true,
  });

  console.log('✅ Bundle listo.\n');

  for (const { id, label } of compositions) {
    console.log(`🎥 Renderizando ${id} — ${label}`);

    const composition = await selectComposition({
      serveUrl: bundleLocation,
      id,
      browserExecutable: '/usr/bin/google-chrome',
    });

    const outputPath = path.join(outDir, `${id}.mp4`);

    await renderMedia({
      composition,
      serveUrl: bundleLocation,
      codec: 'h264',
      outputLocation: outputPath,
      ffmpegPath,
      browserExecutable: '/usr/bin/google-chrome',
      puppeteerArgs: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
      ],
      onProgress: ({ progress }) => {
        const pct = Math.round(progress * 100);
        if (pct % 20 === 0) process.stdout.write(`   ${pct}%... `);
      },
      chromiumOptions: {
        disableWebSecurity: true,
      },
    });

    const size = (fs.statSync(outputPath).size / 1024 / 1024).toFixed(1);
    console.log(`\n   ✓ ${id}.mp4 (${size} MB)`);
  }

  console.log('\n✅ Todos los reels generados en /mp4/');
  console.log('   Formato: 1080x1920px (Instagram Reels 9:16)');
  console.log('   Codec: H264 · 30fps · Faceless\n');
}

main().catch((e) => {
  console.error('\n❌ Error:', e.message);
  process.exit(1);
});
