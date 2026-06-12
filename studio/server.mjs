import express from 'express';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';
import { spawn, execSync } from 'child_process';
import Anthropic from '@anthropic-ai/sdk';
import multer from 'multer';
import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ── Cloudflare R2 Client Configuration ──────────────────────────
const s3Client = process.env.AWS_ACCESS_KEY_ID ? new S3Client({
  endpoint: process.env.AWS_S3_ENDPOINT_URL,
  region: 'auto',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  }
}) : null;

async function uploadFileToR2(filePath, key, contentType) {
  if (!s3Client) {
    console.log(`[R2] Skip upload of ${filePath} because R2 is not configured.`);
    return null;
  }
  try {
    const fileStream = fs.createReadStream(filePath);
    const bucket = process.env.AWS_STORAGE_BUCKET_NAME || 'app-mirrorwork';
    const uploadParams = {
      Bucket: bucket,
      Key: key,
      Body: fileStream,
      ContentType: contentType
    };
    await s3Client.send(new PutObjectCommand(uploadParams));
    console.log(`[R2] Uploaded successfully: ${key}`);
    const publicUrl = `https://${process.env.AWS_S3_CUSTOM_DOMAIN}/${key}`;
    return publicUrl;
  } catch (err) {
    console.error(`[R2] Error uploading ${filePath} to key ${key}:`, err);
    return null;
  }
}

async function downloadDataFromR2(key, localPath) {
  if (!s3Client) return;
  try {
    const bucket = process.env.AWS_STORAGE_BUCKET_NAME || 'app-mirrorwork';
    const response = await s3Client.send(new GetObjectCommand({
      Bucket: bucket,
      Key: key
    }));
    
    // Convert readable stream to file
    const fileStream = fs.createWriteStream(localPath);
    
    await new Promise((resolve, reject) => {
      response.Body.pipe(fileStream);
      response.Body.on('error', reject);
      fileStream.on('finish', resolve);
    });
    
    console.log(`[R2] Successfully downloaded ${key} to ${localPath}`);
  } catch (err) {
    if (err.name !== 'NoSuchKey') {
      console.error(`[R2] Error downloading ${key} to ${localPath}:`, err);
    } else {
      console.log(`[R2] File ${key} not found in R2 (first run fallback).`);
    }
  }
}

const app = express();
const PORT = 3847;


function getChromeExecutable() {
  const possiblePaths = [
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ];
  for (const p of possiblePaths) {
    if (fs.existsSync(p)) return p;
  }
  for (const cmd of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']) {
    try {
      const p = execSync(`which ${cmd}`, { stdio: [] }).toString().trim();
      if (p) return p;
    } catch (e) {}
  }
  return 'google-chrome'; // fallback
}

app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// ── Paths ─────────────────────────────────────────────────────────
const BASE      = path.join(__dirname, '..');
const CONTENIDO = path.join(BASE, 'contenido');
const REELS_DIR = path.join(BASE, 'contenido', 'reels', 'remotion');
const STATE_F   = path.join(__dirname, 'data', 'state.json');
const CONFIG_F  = path.join(__dirname, 'data', 'config.json');
const REPO_DIR  = path.join(__dirname, 'repository');
const ASSETS_DIR= path.join(__dirname, 'assets');

[path.join(__dirname,'data'), REPO_DIR, ASSETS_DIR].forEach(d => fs.mkdirSync(d, { recursive: true }));

// ── Config ────────────────────────────────────────────────────────
function loadConfig() {
  try { return JSON.parse(fs.readFileSync(CONFIG_F, 'utf8')); }
  catch { return {}; }
}
function saveConfig(c) { fs.writeFileSync(CONFIG_F, JSON.stringify(c, null, 2)); }
function getApiKey() { return process.env.GEMINI_API_KEY || process.env.OPENROUTER_API_KEY || process.env.ANTHROPIC_API_KEY || loadConfig().apiKey || null; }

// ── State ─────────────────────────────────────────────────────────
function loadState() {
  try { return JSON.parse(fs.readFileSync(STATE_F, 'utf8')); }
  catch { return {}; }
}
function saveState(s) {
  fs.writeFileSync(STATE_F, JSON.stringify(s, null, 2));
  if (process.env.AWS_ACCESS_KEY_ID) {
    uploadFileToR2(STATE_F, 'cgm/data/state.json', 'application/json').catch(err => {
      console.error('Error uploading state.json to R2:', err);
    });
  }
}

// ── Content definitions (Dynamic JSON Database) ───────────────────
const CAROUSELS_DATA_F = path.join(__dirname, 'data', 'carruseles_data.json');
const REELS_DATA_F = path.join(__dirname, 'data', 'reels_data.json');
const REMOTION_REELS_DATA_F = path.join(BASE, 'contenido', 'reels', 'remotion', 'src', 'reels_data.json');

function loadCarousels() {
  try { return JSON.parse(fs.readFileSync(CAROUSELS_DATA_F, 'utf8')); }
  catch { return []; }
}
function saveCarousels(data) {
  fs.writeFileSync(CAROUSELS_DATA_F, JSON.stringify(data, null, 2));
  uploadFileToR2(CAROUSELS_DATA_F, 'cgm/data/carruseles_data.json', 'application/json').catch(err => {
    console.error('Error uploading carruseles_data.json to R2:', err);
  });
}
function loadReels() {
  try { return JSON.parse(fs.readFileSync(REELS_DATA_F, 'utf8')); }
  catch { return []; }
}
function saveReels(data) {
  fs.writeFileSync(REELS_DATA_F, JSON.stringify(data, null, 2));
  try {
    fs.writeFileSync(REMOTION_REELS_DATA_F, JSON.stringify(data, null, 2));
  } catch (err) {
    console.error('Error syncing Remotion reels_data.json:', err);
  }
  uploadFileToR2(REELS_DATA_F, 'cgm/data/reels_data.json', 'application/json').catch(err => {
    console.error('Error uploading reels_data.json to R2:', err);
  });
}

// Download data from R2 on start if available
if (process.env.AWS_ACCESS_KEY_ID) {
  console.log("[R2] Restoring JSON databases and state from Cloudflare R2...");
  try {
    await downloadDataFromR2('cgm/data/state.json', STATE_F);
    await downloadDataFromR2('cgm/data/carruseles_data.json', CAROUSELS_DATA_F);
    await downloadDataFromR2('cgm/data/reels_data.json', REELS_DATA_F);
    await downloadDataFromR2('cgm/data/reels_data.json', REMOTION_REELS_DATA_F);
  } catch (err) {
    console.error("[R2] Error restoring JSON databases on startup:", err);
  }
}


async function callAI(apiKey, systemPrompt, userMessage) {
  if (apiKey.startsWith('sk-or-')) {
    // OpenRouter
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'HTTP-Referer': 'http://localhost:3847',
        'X-Title': 'Endonautas Content Studio'
      },
      body: JSON.stringify({
        model: 'google/gemini-2.5-pro',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userMessage }
        ],
        response_format: { type: 'json_object' }
      })
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(`OpenRouter Error: ${err}`);
    }
    const data = await response.json();
    return data.choices[0].message.content;
  } else if (apiKey.startsWith('sk-ant-')) {
    // Anthropic legacy
    const anthropic = new Anthropic({ apiKey });
    const message = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-latest',
      max_tokens: 8000,
      system: systemPrompt,
      messages: [{ role: 'user', content: userMessage }]
    });
    return message.content[0].text;
  } else {
    // Native Gemini API
    const model = 'gemini-2.5-pro';
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ role: 'user', parts: [{ text: userMessage }] }],
        systemInstruction: { parts: [{ text: systemPrompt }] },
        generationConfig: { responseMimeType: 'application/json' }
      })
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Gemini Native Error: ${err}`);
    }
    const data = await response.json();
    const txt = data.candidates?.[0]?.content?.parts?.[0]?.text;
    if (!txt) throw new Error('No se recibió texto de Gemini API');
    return txt;
  }
}

const STRATEGIES = {
  'perfil':      { label: 'Perfil', description: 'Presentación de Franco y Endonautas. Se fija en el perfil.' },
  'viralidad':   { label: 'Viralidad', description: 'Idea contraintuitiva que rompe creencia del mercado.' },
  'educacion':   { label: 'Educación', description: 'Conocimiento aplicado con una victoria rápida para el seguidor.' },
  'conexion':    { label: 'Conexión', description: 'Historia personal difícil: "soy como tú".' },
  'creencia':    { label: 'Creencia', description: 'Opinión fuerte que construye comunidad y filtra audiencia.' },
  'autoridad':   { label: 'Autoridad', description: 'Demostrar profundidad y metodología de Endonautas.' },
  'conversion':  { label: 'Conversión', description: 'CTA suave hacia el test "Descubre tu Máscara".' },
  'cotidiano':   { label: 'Cotidiano', description: 'Situación del día a día que eleva conciencia del avatar.' },
};

// ── Multer for image uploads ──────────────────────────────────────
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const dir = path.join(ASSETS_DIR, req.params.carouselId || 'general');
    fs.mkdirSync(dir, { recursive: true });
    cb(null, dir);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    cb(null, `${Date.now()}${ext}`);
  },
});
const upload = multer({ storage, limits: { fileSize: 15 * 1024 * 1024 } });

// ── SSE ───────────────────────────────────────────────────────────
const sseClients = new Set();
app.get('/api/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.write('data: connected\n\n');
  sseClients.add(res);
  req.on('close', () => sseClients.delete(res));
});
function broadcast(event, data) {
  const msg = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  for (const c of sseClients) c.write(msg);
}

// ── Status ────────────────────────────────────────────────────────
app.get('/api/status', (req, res) => {
  const state = loadState();
  const carouselsData = loadCarousels();
  const reelsData = loadReels();

  const carousels = carouselsData.map(c => {
    const hasHtml  = true; // Dynamic template served
    const s = state[c.id] || {};
    const pngDir   = path.join(CONTENIDO, 'carruseles', 'pngs', `${c.id}-${c.file}`);
    let pngCount   = fs.existsSync(pngDir) ? fs.readdirSync(pngDir).filter(f=>f.endsWith('.png')).length : 0;
    if (pngCount === 0 && s.pngCount !== undefined) {
      pngCount = s.pngCount;
    }
    const assetDir = path.join(ASSETS_DIR, c.id);
    const assets   = fs.existsSync(assetDir) ? fs.readdirSync(assetDir).filter(f=>/\.(jpg|jpeg|png|webp|gif)$/i.test(f)) : [];
    return {
      id: c.id,
      title: c.title,
      file: c.file,
      phase: c.phase || 'General',
      slides: c.slides ? c.slides.length : 0,
      hasHtml,
      pngCount,
      assets,
      published: !!s.published,
      publishedAt: s.publishedAt||null,
      notes: s.notes||''
    };
  });

  const reels = reelsData.map(r => {
    const scriptDir = path.join(CONTENIDO, 'reels', 'scripts');
    const hasScript = (fs.existsSync(scriptDir) && fs.readdirSync(scriptDir).some(f=>f.startsWith(`reel-${r.id}-`))) || (r.scenes && r.scenes.length > 0);
    const mp4Path   = path.join(CONTENIDO, 'reels', 'mp4', `${r.id}.mp4`);
    const s = state[r.id] || {};
    let hasVideo  = fs.existsSync(mp4Path);
    let videoSize = hasVideo ? (fs.statSync(mp4Path).size/1024/1024).toFixed(1) : null;
    if (!hasVideo && s.hasVideo) {
      hasVideo = s.hasVideo;
      videoSize = s.videoSize;
    }
    const voiceDir  = path.join(BASE, 'voice');
    const hasVoice  = fs.existsSync(voiceDir) && fs.readdirSync(voiceDir).some(f=>f.toLowerCase().startsWith(r.id.toLowerCase()));
    const s = state[r.id] || {};
    return {
      id: r.id,
      title: r.title,
      duration: `${r.duration || 30}s`,
      hasScript,
      hasVideo,
      videoSize,
      hasVoice,
      hasSfx:!!s.hasSfx,
      hasStockBg:!!s.hasStockBg,
      published:!!s.published,
      publishedAt:s.publishedAt||null,
      notes:s.notes||''
    };
  });

  res.json({ carousels, reels, hasApiKey: !!getApiKey() });
});

app.get('/api/config', (req, res) => {
  const c = loadConfig();
  res.json({
    hasApiKey: !!getApiKey(),
    postizHost: c.postizHost || '',
    postizApiKey: c.postizApiKey ? '********' : '',
    postizChannelId: c.postizChannelId || '',
    makeWebhookUrl: c.makeWebhookUrl || ''
  });
});

app.post('/api/config', (req, res) => {
  const c = loadConfig();
  if (req.body.apiKey) c.apiKey = req.body.apiKey;
  if (req.body.postizHost !== undefined) c.postizHost = req.body.postizHost;
  if (req.body.postizApiKey !== undefined && req.body.postizApiKey !== '********') {
    c.postizApiKey = req.body.postizApiKey;
  }
  if (req.body.postizChannelId !== undefined) c.postizChannelId = req.body.postizChannelId;
  if (req.body.makeWebhookUrl !== undefined) c.makeWebhookUrl = req.body.makeWebhookUrl;
  saveConfig(c);
  res.json({ ok: true });
});

app.patch('/api/state/:id', (req, res) => {
  const state = loadState();
  const prev  = state[req.params.id] || {};
  state[req.params.id] = { ...prev, ...req.body };
  if (req.body.published && !prev.publishedAt) state[req.params.id].publishedAt = new Date().toISOString();
  saveState(state);
  broadcast('state-update', { id: req.params.id });
  res.json({ ok: true });
});

// ── Static file serves ────────────────────────────────────────────
app.get('/preview/carousel/:id', (req, res) => {
  const id = req.params.id.toUpperCase();
  const carousels = loadCarousels();
  const c = carousels.find(x => x.id === id);
  if (!c) return res.status(404).send('Not found');
  const f = path.join(CONTENIDO, 'carruseles', 'html', 'dynamic-carrusel.html');
  if (!fs.existsSync(f)) return res.status(404).send('HTML no generado');
  res.sendFile(f);
});
app.get('/preview/png/:id/:slide', (req, res) => {
  const id = req.params.id.toUpperCase();
  const carousels = loadCarousels();
  const c = carousels.find(x => x.id === id);
  if (!c) return res.status(404).send('Not found');

  if (process.env.AWS_S3_CUSTOM_DOMAIN) {
    const publicUrl = `https://${process.env.AWS_S3_CUSTOM_DOMAIN}/cgm/carruseles/pngs/${c.id}-${c.file}/${req.params.slide}`;
    return res.redirect(publicUrl);
  }

  const f = path.join(CONTENIDO, 'carruseles', 'pngs', `${c.id}-${c.file}`, req.params.slide);
  if (!fs.existsSync(f)) return res.status(404).send('PNG no encontrado');
  res.sendFile(f);
});
app.get('/preview/script/:id', (req, res) => {
  const id = req.params.id.toUpperCase();
  const reels = loadReels();
  const r = reels.find(x => x.id === id);
  if (!r) return res.status(404).send('Not found');
  
  // Try local text script file first
  const dir  = path.join(CONTENIDO, 'reels', 'scripts');
  if (fs.existsSync(dir)) {
    const file = fs.readdirSync(dir).find(f => f.toLowerCase().startsWith(`reel-${id.toLowerCase()}-`));
    if (file) {
      res.setHeader('Content-Type', 'text/plain; charset=utf-8');
      return res.send(fs.readFileSync(path.join(dir, file), 'utf8'));
    }
  }
  
  // Fallback to text representation of scenes
  const lines = [];
  if (r.scenes) {
    r.scenes.forEach((scene, sIdx) => {
      lines.push(`ESCENA ${sIdx + 1} (${scene.from}s - ${scene.from + scene.duration}s):`);
      if (scene.elements) {
        scene.elements.forEach(el => {
          if (el.text) lines.push(`  - ${el.text.replace(/<br\s*\/?>/gi, ' ')}`);
        });
      }
      lines.push('');
    });
  }
  
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.send(lines.join('\n'));
});
app.get('/preview/video/:id', (req, res) => {
  if (process.env.AWS_S3_CUSTOM_DOMAIN) {
    const publicUrl = `https://${process.env.AWS_S3_CUSTOM_DOMAIN}/cgm/reels/mp4/${req.params.id.toUpperCase()}.mp4`;
    return res.redirect(publicUrl);
  }

  const f = path.join(CONTENIDO, 'reels', 'mp4', `${req.params.id.toUpperCase()}.mp4`);
  if (!fs.existsSync(f)) return res.status(404).send('Video no renderizado');
  res.sendFile(f);
});
app.use('/assets', express.static(path.join(__dirname, '..', 'assets')));
app.use('/assets', express.static(ASSETS_DIR));
app.use('/fondos-pexels', express.static(path.join(BASE, 'brand', 'social', 'plantilla', '04-fondos-pexels')));
app.use('/brand-assets', express.static(path.join(BASE, 'brand', 'social', 'plantilla', '_assets')));

// ── Editor APIs ───────────────────────────────────────────────────
app.get('/api/editor/carruseles', (req, res) => {
  res.json(loadCarousels());
});
app.put('/api/editor/carruseles', (req, res) => {
  if (!Array.isArray(req.body)) return res.status(400).json({ error: 'Body must be an array' });
  saveCarousels(req.body);
  broadcast('state-update', {});
  res.json({ ok: true });
});
app.get('/api/editor/reels', (req, res) => {
  res.json(loadReels());
});
app.put('/api/editor/reels', (req, res) => {
  if (!Array.isArray(req.body)) return res.status(400).json({ error: 'Body must be an array' });
  saveReels(req.body);
  broadcast('state-update', {});
  res.json({ ok: true });
});
app.get('/api/carousel-data/:id', (req, res) => {
  const id = req.params.id.toUpperCase();
  const carousels = loadCarousels();
  const c = carousels.find(x => x.id === id);
  if (!c) return res.status(404).json({ error: 'Carrusel no encontrado' });
  res.json(c);
});

// ── Image upload ──────────────────────────────────────────────────
app.post('/api/upload/:carouselId', upload.array('images', 10), async (req, res) => {
  try {
    const files = [];
    for (const f of req.files) {
      const r2Key = `cgm/assets/${req.params.carouselId}/${f.filename}`;
      const r2Url = await uploadFileToR2(f.path, r2Key, f.mimetype);
      files.push({
        name: f.filename,
        url: r2Url || `/assets/${req.params.carouselId}/${f.filename}`,
        size: f.size,
      });
    }
    broadcast('state-update', { id: req.params.carouselId });
    res.json({ ok: true, files });
  } catch (err) {
    console.error('Error in /api/upload/:carouselId:', err);
    res.status(500).json({ error: err.message });
  }
});

// ── Repository ────────────────────────────────────────────────────
app.get('/api/repository', (req, res) => {
  if (!fs.existsSync(REPO_DIR)) return res.json([]);
  const entries = fs.readdirSync(REPO_DIR)
    .filter(d => fs.statSync(path.join(REPO_DIR, d)).isDirectory())
    .map(d => {
      try {
        const meta = JSON.parse(fs.readFileSync(path.join(REPO_DIR, d, 'metadata.json'), 'utf8'));
        return meta;
      } catch { return null; }
    })
    .filter(Boolean)
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  res.json(entries);
});

app.get('/api/repository/:id', (req, res) => {
  const dir = path.join(REPO_DIR, req.params.id);
  if (!fs.existsSync(dir)) return res.status(404).json({ error: 'No encontrado' });
  const meta = JSON.parse(fs.readFileSync(path.join(dir, 'metadata.json'), 'utf8'));
  res.json(meta);
});

app.get('/repo/:id/:file', (req, res) => {
  const f = path.join(REPO_DIR, req.params.id, req.params.file);
  if (!fs.existsSync(f)) return res.status(404).send('Not found');
  res.sendFile(f);
});

// ── HTML carousel builder (server-side template) ──────────────────
// SVG Constellation from brandbook
const svgConstellation = `
  <svg class="const-svg" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <!-- Glow suave para estrellas brillantes -->
      <filter id="gs" x="-80%" y="-80%" width="260%" height="260%">
        <feGaussianBlur stdDeviation="2.2" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <!-- Glow fuerte para Rigel / Betelgeuse -->
      <filter id="gl" x="-120%" y="-120%" width="340%" height="340%">
        <feGaussianBlur stdDeviation="4" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    <g stroke="rgba(126,207,168,0.26)" stroke-width="0.65" fill="none">
      <line x1="672" y1="148" x2="718" y2="262"/>
      <line x1="845" y1="128" x2="794" y2="258"/>
      <line x1="718" y1="262" x2="756" y2="258"/>
      <line x1="756" y1="258" x2="794" y2="258"/>
      <line x1="718" y1="262" x2="695" y2="395"/>
      <line x1="794" y1="258" x2="876" y2="382"/>
    </g>
    <circle cx="876" cy="382" r="4.2" fill="white" opacity="0.96" filter="url(#gl)"/>
    <circle cx="672" cy="148" r="3.6" fill="#ffe8d0" opacity="0.93" filter="url(#gl)"/>
    <circle cx="845" cy="128" r="2.3" fill="white" opacity="0.84" filter="url(#gs)"/>
    <circle cx="756" cy="258" r="2.6" fill="white" opacity="0.90" filter="url(#gs)"/>
    <circle cx="718" cy="262" r="2.4" fill="white" opacity="0.87" filter="url(#gs)"/>
    <circle cx="794" cy="258" r="2.1" fill="white" opacity="0.81" filter="url(#gs)"/>
    <circle cx="695" cy="395" r="2.0" fill="white" opacity="0.80" filter="url(#gs)"/>
    <circle cx="612" cy="192" r="1.4" fill="white" opacity="0.52"/>
    <circle cx="600" cy="224" r="1.1" fill="white" opacity="0.42"/>
    <circle cx="920" cy="190" r="1.2" fill="white" opacity="0.48"/>
    <circle cx="936" cy="312" r="1.0" fill="white" opacity="0.38"/>
    <circle cx="752" cy="204" r="1.0" fill="white" opacity="0.35"/>
    <g stroke="rgba(126,207,168,0.20)" stroke-width="0.60" fill="none">
      <line x1="622" y1="800" x2="684" y2="868"/>
      <line x1="684" y1="868" x2="804" y2="884"/>
      <line x1="804" y1="884" x2="840" y2="812"/>
      <line x1="840" y1="812" x2="622" y2="800"/>
      <line x1="840" y1="812" x2="952" y2="792"/>
      <line x1="952" y1="792" x2="1044" y2="826"/>
      <line x1="1044" y1="826" x2="1068" y2="878"/>
    </g>
    <circle cx="622" cy="800" r="2.4" fill="white" opacity="0.86" filter="url(#gs)"/>
    <circle cx="684" cy="868" r="2.0" fill="white" opacity="0.80"/>
    <circle cx="804" cy="884" r="1.9" fill="white" opacity="0.77"/>
    <circle cx="840" cy="812" r="1.5" fill="white" opacity="0.60"/>
    <circle cx="952" cy="792" r="2.5" fill="white" opacity="0.88" filter="url(#gs)"/>
    <circle cx="1044" cy="826" r="2.1" fill="white" opacity="0.82"/>
    <circle cx="1068" cy="878" r="2.2" fill="white" opacity="0.84" filter="url(#gs)"/>
    <circle cx="118" cy="862" r="3.0" fill="white" opacity="0.88" filter="url(#gs)"/>
    <circle cx="490" cy="192" r="2.2" fill="#ffcca0" opacity="0.72" filter="url(#gs)"/>
    <circle cx="320" cy="96" r="2.0" fill="#ffe8c0" opacity="0.68" filter="url(#gs)"/>
    <circle cx="968" cy="512" r="1.8" fill="white" opacity="0.65" filter="url(#gs)"/>
    <circle cx="548" cy="298" r="1.6" fill="#ffd8b0" opacity="0.60"/>
    <circle cx="518" cy="274" r="1.3" fill="white" opacity="0.55"/>
    <circle cx="144" cy="450" r="1.5" fill="#7ecfa8" opacity="0.58" filter="url(#gs)"/>
    <circle cx="966" cy="648" r="1.3" fill="#7ec8cf" opacity="0.50"/>
  </svg>
`;

function buildCarouselHTML({ id, title, slides, caption, phase, strategy, theme }) {
  const N = slides.length;
  // Theme selection: if not B or C, fallback to odd = Theme B, even = Theme C
  const isThemeC = theme === 'C' || (theme !== 'B' && id && parseInt(id.replace(/\D/g, '')) % 2 === 0);
  
  const bgUrl = isThemeC 
    ? '/fondos-pexels/dark-galaxy-3-33931033.jpg' 
    : '/fondos-pexels/nebula-space-dark-3-33931036.jpg';

  const slideDivs = slides.map((s, i) => {
    const active = i === 0 ? ' active' : '';
    
    const isHook = i === 0 || s.type === 'hook';
    const isCta = i === N - 1 || s.type === 'cta';
    const isQuote = s.type === 'quote';

    let bgFilter = 'brightness(0.72) contrast(1.12) saturate(0.28)'; // Theme C default
    if (!isThemeC) {
      if (isHook) bgFilter = 'brightness(0.65) contrast(1.18) saturate(0.55) hue-rotate(15deg)';
      else if (isQuote) bgFilter = 'brightness(0.52) contrast(1.22) saturate(0.45) hue-rotate(15deg)';
      else if (isCta) bgFilter = 'brightness(0.58) contrast(1.18) saturate(0.48) hue-rotate(15deg)';
      else bgFilter = 'brightness(0.58) contrast(1.20) saturate(0.50) hue-rotate(15deg)';
    }

    let topNav = '';
    if (isThemeC) {
      topNav = `
        <div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;display:flex;align-items:center;justify-content:space-between;width:calc(100% - 128px);">
          <div style="display:flex;align-items:center;gap:10px;">
            <img style="width:30px;height:30px;border-radius:50%;" src="/brand-assets/logo-trans.png">
            <span style="font-weight:700;font-size:16px;letter-spacing:0.04em;color:rgba(240,232,220,0.72);">Endonautas</span>
          </div>
          <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.24em;color:rgba(240,232,220,0.28);text-transform:uppercase;">
            ${strategy || phase || 'Vínculos · Patrones'}
          </span>
        </div>`;
    } else {
      topNav = `
        <div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;display:flex;align-items:center;justify-content:space-between;width:calc(100% - 128px);">
          <div style="display:flex;align-items:center;gap:10px;">
            <img style="width:30px;height:30px;border-radius:50%;" src="/brand-assets/logo-trans.png">
            <span style="font-weight:700;font-size:16px;letter-spacing:0.04em;color:rgba(240,232,220,0.75);">Endonautas</span>
          </div>
          <div style="border:1px solid rgba(126,207,168,0.30);border-radius:2px;padding:8px 16px;font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.24em;text-transform:uppercase;color:rgba(126,207,168,0.65);">
            ${strategy || phase || 'VÍNCULOS · PATRONES'}
          </div>
        </div>`;
    }

    let innerContent = '';
    
    if (isHook) {
      // ── Portada / Hook Slide ──
      const titleClean = (s.headline || '').replace(/_([^_]+)_/g, '<em>$1</em>').replace(/\*([^*]+)\*/g, '<em>$1</em>');
      if (isThemeC) {
        innerContent = `
          <div style="position:absolute;left:64px;right:0;bottom:52px;z-index:10;text-align:left;">
            <h1 style="font-weight:900;font-size:128px;line-height:0.85;letter-spacing:-0.05em;color:#F0E8DC;margin-bottom:30px;">
              ${titleClean}
            </h1>
            <div style="width:calc(100% - 0px);height:1px;background:linear-gradient(to right,rgba(126,207,168,0.50),transparent);margin-bottom:22px;margin-right:64px;"></div>
            <p style="font-family:'Plus Jakarta Sans';font-size:24px;line-height:1.52;color:rgba(240,232,220,0.48);max-width:520px;padding-right:64px;margin-bottom:24px;">
              ${s.body || ''}
            </p>
            <div style="display:flex;padding-right:64px;justify-content:space-between;align-items:center;">
              <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;color:rgba(126,207,168,0.65);text-transform:uppercase;">
                ${s.ctaText || 'Desliza →'}
              </span>
              <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">${String(i + 1).padStart(2, '0')} / ${String(N).padStart(2, '0')}</span>
            </div>
          </div>
        `;
      } else {
        innerContent = `
          <div style="position:absolute;left:64px;right:64px;bottom:52px;z-index:10;text-align:left;">
            <div style="display:inline-block;background:rgba(126,207,168,0.10);border-left:3px solid #7ecfa8;padding:9px 18px;margin-bottom:24px;">
              <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.28em;text-transform:uppercase;color:#7ecfa8;">
                ${s.eyebrow || strategy || phase || 'Post 01 de 09'}
              </span>
            </div>
            <h1 style="font-weight:900;font-size:104px;line-height:0.87;letter-spacing:-0.042em;color:#F0E8DC;margin-bottom:30px;">
              ${titleClean}
            </h1>
            <p style="font-family:'Plus Jakarta Sans';font-size:24px;line-height:1.55;color:rgba(240,232,220,0.52);max-width:520px;margin-bottom:28px;">
              ${s.body || ''}
            </p>
            <div style="display:flex;align-items:center;justify-content:space-between;">
              <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;color:rgba(126,207,168,0.60);text-transform:uppercase;">
                ${s.ctaText || 'Desliza para ver →'}
              </span>
              <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">${String(i + 1).padStart(2, '0')} / ${String(N).padStart(2, '0')}</span>
            </div>
          </div>
        `;
      }
    } else if (isCta) {
      // ── CTA Slide ──
      const titleClean = (s.headline || '').replace(/_([^_]+)_/g, '<em>$1</em>').replace(/\*([^*]+)\*/g, '<em>$1</em>');
      if (isThemeC) {
        innerContent = `
          <div style="position:absolute;left:64px;right:64px;bottom:52px;z-index:10;text-align:left;">
            <h2 style="font-weight:900;font-size:118px;line-height:0.84;letter-spacing:-0.05em;color:#F0E8DC;margin-bottom:28px;">
              ${titleClean}
            </h2>
            <p style="font-family:'Plus Jakarta Sans';font-size:24px;line-height:1.55;color:rgba(240,232,220,0.46);max-width:500px;margin-bottom:44px;">
              ${s.body || ''}
            </p>
            <div style="display:flex;align-items:center;gap:32px;">
              <div style="padding:18px 44px;border-radius:60px;background:#7ecfa8;color:#030c07;font-weight:700;font-size:14px;letter-spacing:0.12em;text-transform:uppercase;box-shadow:0 0 80px rgba(126,207,168,0.48),0 0 160px rgba(126,207,168,0.16);">
                ${s.ctaText || 'COMENZAR EN ENDONAUTAS.CL →'}
              </div>
              <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.22);">${String(i + 1).padStart(2, '0')} / ${String(N).padStart(2, '0')}</span>
            </div>
          </div>
        `;
      } else {
        innerContent = `
          <div style="position:absolute;left:64px;right:64px;bottom:52px;z-index:10;text-align:left;">
            <div style="display:inline-block;background:rgba(126,207,168,0.10);border-left:3px solid #7ecfa8;padding:9px 18px;margin-bottom:22px;">
              <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.28em;text-transform:uppercase;color:#7ecfa8;">
                ${s.eyebrow || 'Mapa Interior'}
              </span>
            </div>
            <h2 style="font-weight:900;font-size:96px;line-height:0.87;letter-spacing:-0.042em;color:#F0E8DC;margin-bottom:26px;">
              ${titleClean}
            </h2>
            <p style="font-family:'Plus Jakarta Sans';font-size:23px;line-height:1.55;color:rgba(240,232,220,0.48);max-width:480px;margin-bottom:40px;">
              ${s.body || ''}
            </p>
            <div style="display:flex;align-items:center;justify-content:space-between;">
              <div style="padding:18px 44px;border-radius:60px;background:#7ecfa8;color:#030c07;font-weight:700;font-size:14px;letter-spacing:0.12em;text-transform:uppercase;box-shadow:0 0 80px rgba(126,207,168,0.45),0 0 160px rgba(126,207,168,0.15);">
                ${s.ctaText || 'COMENZAR EN ENDONAUTAS.CL →'}
              </div>
              <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.22);">${String(i + 1).padStart(2, '0')} / ${String(N).padStart(2, '0')}</span>
            </div>
          </div>
        `;
      }
    } else if (isQuote) {
      // ── Cita / Impacto Slide ──
      let quoteLine1 = '';
      let quoteLine2 = (s.headline || '').replace(/_([^_]+)_/g, '<em>$1</em>').replace(/\*([^*]+)\*/g, '<em>$1</em>');
      if (s.headline && s.headline.includes('\n')) {
        const parts = s.headline.split('\n');
        quoteLine1 = parts[0].trim().replace(/_([^_]+)_/g, '<em>$1</em>').replace(/\*([^*]+)\*/g, '<em>$1</em>');
        quoteLine2 = parts.slice(1).join('\n').trim().replace(/_([^_]+)_/g, '<em>$1</em>').replace(/\*([^*]+)\*/g, '<em>$1</em>');
      }

      if (isThemeC) {
        innerContent = `
          <div style="position:absolute;left:64px;right:64px;top:0;bottom:0;z-index:10;display:flex;flex-direction:column;justify-content:center;padding-top:40px;text-align:left;">
            <div style="font-size:200px;line-height:0.45;font-weight:900;color:rgba(126,207,168,0.15);margin-left:-10px;margin-bottom:24px;">&ldquo;</div>
            ${quoteLine1 ? `
            <p style="font-family:'Plus Jakarta Sans';font-size:52px;font-weight:300;line-height:1.05;color:rgba(240,232,220,0.52);letter-spacing:-0.015em;margin-bottom:4px;">
              ${quoteLine1}
            </p>` : ''}
            <p style="font-size:92px;font-weight:900;line-height:0.88;letter-spacing:-0.046em;color:#F0E8DC;margin-bottom:40px;">
              ${quoteLine2}
            </p>
            <div style="display:flex;align-items:center;gap:18px;margin-bottom:26px;">
              <div style="width:50px;height:1.5px;background:#7ecfa8;opacity:0.65;"></div>
              <div style="width:7px;height:7px;border-radius:50%;background:#7ecfa8;opacity:0.55;"></div>
            </div>
            <p style="font-family:'Plus Jakarta Sans';font-size:25px;line-height:1.48;color:rgba(240,232,220,0.36);font-style:italic;">
              ${s.body || ''}
            </p>
          </div>
          <div style="position:absolute;bottom:52px;left:64px;right:64px;z-index:10;display:flex;justify-content:space-between;">
            <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;color:rgba(126,207,168,0.60);text-transform:uppercase;">Continúa →</span>
            <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">${String(i + 1).padStart(2, '0')} / ${String(N).padStart(2, '0')}</span>
          </div>
        `;
      } else {
        innerContent = `
          <!-- SVG Accent Lines -->
          <svg style="position:absolute;inset:0;width:100%;height:100%;z-index:5;" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="hl" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stop-color="#7ecfa8" stop-opacity="0"/>
                <stop offset="35%" stop-color="#7ecfa8" stop-opacity="0.35"/>
                <stop offset="65%" stop-color="#7ecfa8" stop-opacity="0.35"/>
                <stop offset="100%" stop-color="#7ecfa8" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <line x1="0" y1="360" x2="1080" y2="360" stroke="url(#hl)" stroke-width="1"/>
            <line x1="0" y1="820" x2="1080" y2="820" stroke="url(#hl)" stroke-width="1"/>
          </svg>
          <div style="position:absolute;left:64px;right:64px;top:0;bottom:0;z-index:10;display:flex;flex-direction:column;justify-content:center;padding-top:80px;text-align:left;">
            <div style="font-size:150px;line-height:0.5;font-weight:900;color:rgba(126,207,168,0.18);margin-left:-8px;margin-bottom:28px;">&ldquo;</div>
            ${quoteLine1 ? `
            <p style="font-family:'Plus Jakarta Sans';font-size:48px;font-weight:300;line-height:1.06;color:rgba(240,232,220,0.55);letter-spacing:-0.01em;margin-bottom:6px;">
              ${quoteLine1}
            </p>` : ''}
            <p style="font-size:80px;font-weight:900;line-height:0.90;letter-spacing:-0.042em;color:#F0E8DC;margin-bottom:36px;">
              ${quoteLine2}
            </p>
            <div style="width:72px;height:1.5px;background:#7ecfa8;opacity:0.60;margin-bottom:28px;"></div>
            <p style="font-family:'Plus Jakarta Sans';font-size:24px;line-height:1.50;color:rgba(240,232,220,0.40);font-style:italic;">
              ${s.body || ''}
            </p>
          </div>
          <div style="position:absolute;bottom:52px;left:64px;right:64px;z-index:10;display:flex;justify-content:space-between;">
            <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;color:rgba(126,207,168,0.60);text-transform:uppercase;">Continúa →</span>
            <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">${String(i + 1).padStart(2, '0')} / ${String(N).padStart(2, '0')}</span>
          </div>
        `;
      }
    } else {
      // ── Content / Desarrollo Slide ──
      const titleClean = (s.headline || '').replace(/_([^_]+)_/g, '<em>$1</em>').replace(/\*([^*]+)\*/g, '<em>$1</em>');
      
      let bodyMain = s.body || '';
      let bodyKey = '';
      if (bodyMain.includes('\n')) {
        const parts = bodyMain.split(/\n+/);
        bodyMain = parts[0].trim();
        bodyKey = parts.slice(1).join('\n').trim();
      }
 
      let keyCard = '';
      if (bodyKey) {
        if (isThemeC) {
          keyCard = `
            <div style="border-top:1px solid rgba(126,207,168,0.18);border-bottom:1px solid rgba(126,207,168,0.10);padding:16px 0;margin-bottom:22px;">
              <div style="font-family:'Plus Jakarta Sans';font-size:11px;letter-spacing:0.32em;text-transform:uppercase;color:#7ecfa8;opacity:0.75;margin-bottom:8px;">CLAVE</div>
              <div style="font-family:'Plus Jakarta Sans';font-size:21px;line-height:1.48;color:rgba(240,232,220,0.60);">${bodyKey}</div>
            </div>`;
        } else {
          keyCard = `
            <div style="background:rgba(126,207,168,0.07);border:1px solid rgba(126,207,168,0.16);border-left:3px solid #7ecfa8;border-radius:0 3px 3px 0;padding:16px 20px;max-width:560px;margin-bottom:24px;">
              <div style="font-family:'Plus Jakarta Sans';font-size:11px;letter-spacing:0.32em;text-transform:uppercase;color:#7ecfa8;margin-bottom:8px;">CLAVE</div>
              <div style="font-family:'Plus Jakarta Sans';font-size:21px;line-height:1.48;color:rgba(240,232,220,0.70);">${bodyKey}</div>
            </div>`;
        }
      }
 
      if (isThemeC) {
        innerContent = `
          <div style="position:absolute;left:64px;top:160px;width:3px;height:500px;z-index:9;background:linear-gradient(to bottom,#7ecfa8,rgba(126,207,168,0.08));"></div>
          <div style="position:absolute;left:88px;right:64px;bottom:52px;z-index:10;text-align:left;">
            <div style="font-size:14px;font-weight:500;letter-spacing:0.22em;color:rgba(126,207,168,0.50);text-transform:uppercase;margin-bottom:26px;font-family:'Plus Jakarta Sans';">
              ${String(i + 1).padStart(2, '0')} ── ${s.tag || 'DESARROLLO'}
            </div>
            <h2 style="font-weight:900;font-size:96px;line-height:0.86;letter-spacing:-0.044em;color:#F0E8DC;margin-bottom:26px;">
              ${titleClean}
            </h2>
            <p style="font-family:'Plus Jakarta Sans';font-size:23px;line-height:1.58;color:rgba(240,232,220,0.48);max-width:560px;margin-bottom:28px;">
              ${bodyMain}
            </p>
            ${keyCard}
            <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;color:rgba(126,207,168,0.65);text-transform:uppercase;">Continúa →</span>
          </div>
        `;
      } else {
        innerContent = `
          <div style="position:absolute;left:64px;right:64px;bottom:52px;z-index:10;text-align:left;">
            <div style="display:flex;align-items:center;gap:16px;margin-bottom:22px;">
              <span style="font-size:56px;font-weight:900;color:#7ecfa8;line-height:1;opacity:0.75;">${String(i + 1).padStart(2, '0')}</span>
              <div style="width:1px;height:52px;background:rgba(126,207,168,0.25);"></div>
              <span style="font-family:'Plus Jakarta Sans';font-size:13px;letter-spacing:0.26em;text-transform:uppercase;color:rgba(240,232,220,0.35);">
                ${s.tag || 'DESARROLLO'}
              </span>
            </div>
            <h2 style="font-weight:900;font-size:80px;line-height:0.88;letter-spacing:-0.036em;color:#F0E8DC;margin-bottom:22px;">
              ${titleClean}
            </h2>
            <p style="font-family:'Plus Jakarta Sans';font-size:23px;line-height:1.58;color:rgba(240,232,220,0.50);max-width:560px;margin-bottom:24px;">
              ${bodyMain}
            </p>
            ${keyCard}
            <div style="display:flex;justify-content:space-between;">
              <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;color:rgba(126,207,168,0.60);text-transform:uppercase;">Continúa →</span>
              <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">${String(i + 1).padStart(2, '0')} / ${String(N).padStart(2, '0')}</span>
            </div>
          </div>
        `;
      }
    }

    return `
      <div class="slide${active}" id="s${i+1}" style="position:absolute;inset:0;display:${i===0?'flex':'none'};flex-direction:column;background:#040810;overflow:hidden;width:1080px;height:1080px;box-sizing:border-box;">
        <div style="position:absolute;inset:0;z-index:1;background:url('${bgUrl}')center/cover;filter:${bgFilter};"></div>
        <div style="position:absolute;inset:0;z-index:2;background:linear-gradient(to top, ${isThemeC ? 'rgba(3,6,12,0.96) 0%, rgba(3,6,12,0.75) 42%, rgba(3,6,12,0.30) 62%, rgba(3,6,12,0.0) 100%' : 'rgba(4,6,14,0.96) 0%, rgba(4,6,14,0.75) 35%, rgba(4,6,14,0.30) 55%, rgba(4,6,14,0.0) 100%'});"></div>
        ${isCta ? `<div style="position:absolute;inset:0;z-index:3;background:radial-gradient(ellipse 85% 60% at 50% 110%, ${isThemeC ? 'rgba(6,48,36,0.52)' : 'rgba(8,55,42,0.55)'} 0%,transparent 58%);"></div>` : ''}
        <div style="position:absolute;inset:0;opacity:${isThemeC ? 0.07 : 0.08};mix-blend-mode:overlay;pointer-events:none;z-index:8;background-image:url('data:image/svg+xml,%3Csvg viewBox=\'0 0 256 256\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.85\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3CfeColorMatrix type=\'saturate\' values=\'0\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\'/%3E%3C/svg%3E');background-size:256px;"></div>
        ${!isThemeC ? `<div style="position:absolute;left:0;top:0;bottom:0;width:4px;z-index:10;background:linear-gradient(to bottom,transparent 8%,#7ecfa8 25%,#7ecfa8 75%,transparent 92%);opacity:0.65;"></div>` : ''}
        ${topNav}
        ${innerContent}
      </div>
    `;
  }).join('\n');

  const allText = slides.map((s, i) => {
    const parts = [s.headline, s.body].filter(Boolean).join('\n');
    return `SLIDE ${i+1} (${s.type})\n${parts}`;
  }).join('\n\n');

  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${id} — ${title} · Endonautas</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:ital,wght@0,300;0,400;0,700;0,900;1,900&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:#1a1a1a;font-family:'Plus Jakarta Sans',sans-serif;display:flex;gap:0;min-height:100vh}
.viewer{flex:0 0 420px;display:flex;flex-direction:column;align-items:center;padding:2rem;background:#111;border-right:1px solid #222}
.slide-viewport{position:relative;width:360px;height:360px;overflow:hidden;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,.6)}
.slide-wrap{position:absolute;top:0;left:0;width:1080px;height:1080px;transform:scale(0.333333);transform-origin:top left}
.slide{position:absolute;inset:0;display:none;flex-direction:column;background:#040810;overflow:hidden;width:1080px;height:1080px}
.slide.active{display:flex}
em{font-style:italic;color:#7ecfa8;-webkit-text-fill-color:#7ecfa8;background:none;-webkit-background-clip:initial;}
.bottom{display:flex;align-items:center;justify-content:space-between;border-top:1px solid rgba(255,255,255,0.07);padding-top:22px;width:100%}
.swipe{font-family:'Plus Jakarta Sans';font-size:11px;font-weight:500;color:rgba(126,207,168,0.65);letter-spacing:0.14em;text-transform:uppercase}
.slide-info{display:flex;align-items:center;gap:18px}
.dots{display:flex;gap:5px;align-items:center}
.dot{width:5px;height:5px;border-radius:50%;background:rgba(240,232,220,0.14);transition:all .3s;cursor:pointer}
.dot.active{background:#7ecfa8;width:20px;border-radius:3px}
.slide-num{font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.24em;color:rgba(240,232,220,0.22);text-transform:uppercase}
.nav-row{display:flex;gap:1rem;margin-top:1rem}
.btn{padding:.5rem 1.2rem;border:1px solid rgba(126,207,168,0.25);border-radius:8px;background:transparent;color:#7ecfa8;font-size:.8rem;font-family:'Plus Jakarta Sans',sans-serif;cursor:pointer;transition:all .2s}
.btn:hover{background:#7ecfa8;color:#000}
.btn:disabled{opacity:.3;cursor:default}
.slide-counter{color:rgba(240,232,220,0.4);font-size:.75rem;margin-top:.8rem;letter-spacing:.1em}
.panel{flex:1;padding:2rem;overflow-y:auto;background:#0d0d0d;color:#F0E8DC}
.panel h2{font-family:'Space Grotesk',sans-serif;font-weight:700;color:#7ecfa8;font-size:1.1rem;margin-bottom:1.5rem;padding-bottom:.8rem;border-bottom:1px solid #222}
.all-text{font-size:.82rem;color:#888;line-height:1.8;white-space:pre-wrap}
.caption-box{margin-top:2rem;padding:1.2rem;border:1px solid #222;border-radius:10px;background:#111}
.caption-box h3{color:#7ecfa8;font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;margin-bottom:.8rem}
.caption-text{font-size:.8rem;color:#777;line-height:1.7;white-space:pre-wrap}
.download-btn{margin-top:1.5rem;padding:.7rem 1.5rem;border:1px solid #7ecfa8;border-radius:8px;background:transparent;color:#7ecfa8;font-size:.8rem;font-family:'Plus Jakarta Sans',sans-serif;cursor:pointer;transition:all .2s;width:100%}
.download-btn:hover{background:#7ecfa8;color:#000}

/* CAPTURE MODE STYLE */
body.capture-mode {
  background:#000;
  padding:0;
  margin:0;
  min-height:auto;
}
body.capture-mode .viewer {
  padding:0;
  background:transparent;
  border:none;
  flex:none;
  width:1080px;
  height:1080px;
}
body.capture-mode .slide-viewport {
  width:1080px;
  height:1080px;
  border-radius:0;
  box-shadow:none;
}
body.capture-mode .slide-wrap {
  transform:none;
  border-radius:0;
  box-shadow:none;
}
body.capture-mode .progress,
body.capture-mode .nav-row,
body.capture-mode .slide-counter,
body.capture-mode .copy-slide,
body.capture-mode .panel {
  display:none !important;
}
</style>
</head>
<body>
<div class="viewer">
  <div class="slide-viewport">
    <div class="slide-wrap" id="slideWrap">${slideDivs}</div>
  </div>
  <div class="nav-row">
    <button class="btn" id="btnPrev" onclick="prev()" disabled>←</button>
    <button class="btn" onclick="next()">→</button>
  </div>
  <div class="slide-counter" id="counter">1 / ${N}</div>
</div>
<div class="panel">
  <h2>${id} — ${title}</h2>
  <div class="all-text">${allText.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>
  <div class="caption-box">
    <h3>Caption Instagram</h3>
    <div class="caption-text">${(caption||'').replace(/</g,'&lt;')}</div>
  </div>
  <button class="download-btn" onclick="downloadTxt()">Descargar TXT</button>
</div>
<script>
if (window.location.search.includes('capture=true')) {
  document.body.classList.add('capture-mode');
}

let cur = 0;
const slides = document.querySelectorAll('.slide');
const N = ${N};
function goTo(i) {
  slides[cur].style.display = 'none';
  slides[cur].classList.remove('active');
  cur = i;
  slides[cur].style.display = 'flex';
  slides[cur].classList.add('active');
  document.getElementById('counter').textContent = (cur+1) + ' / ' + N;
  document.getElementById('btnPrev').disabled = cur === 0;
}
function prev() { if(cur>0) goTo(cur-1); }
function next() { if(cur<N-1) goTo(cur+1); }
document.addEventListener('keydown', e => { if(e.key==='ArrowRight') next(); if(e.key==='ArrowLeft') prev(); });
function downloadTxt() {
  const t = ${JSON.stringify(allText + '\n\nCAPTION:\n' + (caption||''))};
  const a = document.createElement('a');
  a.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(t);
  a.download = '${id}-${title.replace(/[^a-z0-9]/gi,'-')}.txt';
  a.click();
}
</script>
</body>
</html>`;
}

// ── AI Generation ─────────────────────────────────────────────────
const BRAND_CONTEXT = `
MARCA: Endonautas — plataforma de autoconocimiento profundo.
AUTOR: Franco Jeria Castro — terapeuta en salud integrativa, escritor de "Endonautica".
ESENCIA: Psicología Jungiana aplicada. Las 12 Dimensiones del ser. Las Máscaras como identidades construidas para sobrevivir.
TONO: íntimo, filosófico, honesto, no motivacional ni "positivo-tóxico". No da consejos. Hace preguntas. Revela lo que el seguidor ya sabe pero no se ha atrevido a nombrar.
AUDIENCIA: personas de 28-50 años que sienten que hay algo más profundo en ellos por explorar. Profesionales, curiosos, introvertidos, en momentos de transición vital.
ESTÉTICA: negro profundo (#0a0a0a), oro antiguo (#c9a84c), tipografía serif elegante (Playfair Display), máximo 40 palabras por slide.
CTA PRINCIPAL: "Comenta MASCARA" — esto activa el test gratuito "Descubre tu Máscara" (el leadmagnet principal).
EVITAR: frases motivacionales, exclamaciones, emojis en los slides, lenguaje de coach, promesas de transformación.
`;

const SLIDE_TYPES = `
Tipos de slide disponibles:
- "hook": slide 1, detiene el scroll. Campo "headline" es la frase principal (max 15 palabras). Puede tener "body" corto.
- "content": desarrollo del concepto. "headline" + "body" (max 30 palabras combinado). Opcional: "tag" (etiqueta pequeña arriba).
- "quote": cita o frase filosófica impactante. Solo "headline" en formato de cita.
- "cta": slide final. "headline" invita a comentar + "body" explica qué recibirán.
`;

app.post('/api/generate', async (req, res) => {
  const apiKey = getApiKey();
  if (!apiKey) return res.status(401).json({ error: 'API key no configurada. Ve a Configuración.' });

  const { prompt, strategy, count = 3, style, references = [] } = req.body;
  if (!prompt) return res.status(400).json({ error: 'Falta el prompt' });

  const strategyCtx = strategy ? `\nESTRATEGIA DE CONTENIDO: ${STRATEGIES[strategy]?.label} — ${STRATEGIES[strategy]?.description}` : '';
  const styleCtx    = style ? `\nESTILO: ${style}` : '';
  const refCtx      = references.filter(Boolean).length > 0 ? `\nREFERENCIAS VISUALES (URLs para inspirarte en estructura y tono): ${references.filter(Boolean).join(', ')}` : '';

  const systemPrompt = `Eres un experto en contenido de Instagram para la marca Endonautas.\n\n${BRAND_CONTEXT}\n${SLIDE_TYPES}

Responde SOLO con un objeto JSON válido (sin markdown, sin texto extra):
{
  "carousels": [
    {
      "id": "gen-001",
      "title": "Título del carrusel",
      "phase": "Viralidad",
      "slides": [
        { "type": "hook", "headline": "...", "body": "..." },
        { "type": "content", "headline": "...", "body": "...", "tag": "opcional" },
        { "type": "quote", "headline": "..." },
        { "type": "content", "headline": "...", "body": "..." },
        { "type": "cta", "headline": "...", "body": "..." }
      ],
      "caption": "Caption completo para Instagram con emojis y hashtags (400-600 caracteres)"
    }
  ]
}`;

  const userMessage = `Crea ${count} carrusel(es) de Instagram con estas instrucciones:\n\n${prompt}${strategyCtx}${styleCtx}${refCtx}\n\nCada carrusel debe tener entre 5 y 9 slides. Varía la estructura entre carruseles si son más de uno.`;

  try {
    broadcast('log', { text: `▶ Generando ${count} carrusel(es) con IA...\n`, type: 'info' });
    const rawText = await callAI(apiKey, systemPrompt, userMessage);
    const raw = rawText.trim();
    let data;
    try {
      data = JSON.parse(raw);
    } catch {
      const match = raw.match(/\{[\s\S]+\}/);
      if (!match) throw new Error('La IA no devolvió JSON válido');
      data = JSON.parse(match[0]);
    }

    const now = new Date();
    const dateStr = now.toISOString().slice(0,19).replace(/[:T]/g,'-');
    const slug = prompt.slice(0,35).replace(/[^a-zA-Z0-9áéíóúñü\s]/g,'').trim().replace(/\s+/g,'-').toLowerCase();
    const repoId = `${dateStr}_${slug}`;
    const repoPath = path.join(REPO_DIR, repoId);
    fs.mkdirSync(repoPath, { recursive: true });

    // Load current editable carousels
    const currentCarousels = loadCarousels();
    let nextNum = 10;
    currentCarousels.forEach(c => {
      const match = c.id.match(/^C(\d+)$/);
      if (match) {
        const val = parseInt(match[1]);
        if (val >= nextNum) nextNum = val + 1;
      }
    });

    const carousels = data.carousels.map((c, i) => {
      const cNum = nextNum + i;
      const cleanSlug = c.title.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]/g, "-").replace(/-+/g, "-").trim();
      return {
        ...c,
        id: `C${cNum}`,
        file: cleanSlug || `carousel-${cNum}`,
        htmlFile: `C${cNum}.html`,
      };
    });

    carousels.forEach(c => {
      const html = buildCarouselHTML({ ...c, strategy: STRATEGIES[strategy]?.label });
      fs.writeFileSync(path.join(repoPath, c.htmlFile), html);
    });

    // Save to dynamic editable carousels database!
    saveCarousels([...currentCarousels, ...carousels.map(c => ({
      id: c.id,
      title: c.title,
      file: c.file,
      phase: c.phase || 'General',
      slides: c.slides,
      caption: c.caption || ''
    }))]);

    const meta = {
      id: repoId,
      prompt,
      strategy: strategy ? STRATEGIES[strategy]?.label : null,
      style,
      count: carousels.length,
      createdAt: now.toISOString(),
      carousels: carousels.map(c => ({ id: c.id, title: c.title, phase: c.phase, htmlFile: c.htmlFile, slides: c.slides.length })),
    };
    fs.writeFileSync(path.join(repoPath, 'metadata.json'), JSON.stringify(meta, null, 2));

    broadcast('log', { text: `✓ ${carousels.length} carrusel(es) generados y guardados\n`, type: 'success' });
    broadcast('action-done', { action: 'generate', repoId });
    res.json({ ok: true, repoId, meta });

  } catch(e) {
    broadcast('log', { text: `✗ Error: ${e.message}\n`, type: 'error' });
    res.status(500).json({ error: e.message });
  }
});

// ── Viral Lab ─────────────────────────────────────────────────────
app.post('/api/viral-score', async (req, res) => {
  const apiKey = getApiKey();
  if (!apiKey) return res.status(401).json({ error: 'API key no configurada' });

  const { text, type = 'carousel' } = req.body;
  if (!text?.trim()) return res.status(400).json({ error: 'Falta el texto a evaluar' });

  try {
    const systemPrompt = "Eres un experto en contenido viral para Instagram especializado en la marca Endonautas (autoconocimiento, psicología Jungiana, audiencia adulta reflexiva).";
    const prompt = `Evalúa el siguiente ${type === 'reel' ? 'guion de reel' : 'carrusel'} y devuelve SOLO un JSON con esta estructura (sin markdown):

{
  "scores": {
    "hook": { "score": 0-10, "comment": "una línea" },
    "emocion": { "score": 0-10, "comment": "una línea" },
    "claridad": { "score": 0-10, "comment": "una línea" },
    "cta": { "score": 0-10, "comment": "una línea" },
    "marca": { "score": 0-10, "comment": "una línea" },
    "viralidad": { "score": 0-10, "comment": "una línea" }
  },
  "total": 0-100,
  "nivel": "Bajo potencial | Buen potencial | Alto potencial | Viral",
  "fortaleza": "Lo mejor del contenido en una oración",
  "mejora": "La única cosa más importante a cambiar, específica y accionable",
  "version_mejorada": "Reescribe solo el hook (slide 1 o primera línea) con el potencial máximo"
}

CONTENIDO A EVALUAR:
${text}`;

    const rawText = await callAI(apiKey, systemPrompt, prompt);
    const raw = rawText.trim();
    let result;
    try { result = JSON.parse(raw); }
    catch {
      const match = raw.match(/\{[\s\S]+\}/);
      result = JSON.parse(match[0]);
    }

    res.json(result);
  } catch(e) {
    res.status(500).json({ error: e.message });
  }
});

// ── Postiz Integration ─────────────────────────────────────────────
app.post('/api/postiz/publish', async (req, res) => {
  const { id, caption, mode, date } = req.body;
  const config = loadConfig();

  if (!config.postizHost || !config.postizApiKey || !config.postizChannelId) {
    return res.status(400).json({ error: 'Configuración de Postiz incompleta. Configúrala en el panel lateral de Configuración.' });
  }

  let mediaFiles = [];
  let isReel = !id.startsWith('C');

  if (!isReel) {
    const carousels = loadCarousels();
    const c = carousels.find(x => x.id === id);
    if (!c) return res.status(404).json({ error: 'Carrusel no encontrado' });
    const pngDir = path.join(CONTENIDO, 'carruseles', 'pngs', `${c.id}-${c.file}`);
    if (fs.existsSync(pngDir)) {
      const files = fs.readdirSync(pngDir).filter(f => f.endsWith('.png')).sort();
      mediaFiles = files.map(f => path.join(pngDir, f));
    }
    if (mediaFiles.length === 0) {
      return res.status(400).json({ error: 'No se encontraron PNGs generados para este carrusel. Genéralos primero.' });
    }
  } else {
    const reels = loadReels();
    const r = reels.find(x => x.id === id);
    if (!r) return res.status(404).json({ error: 'Reel no encontrado' });
    const mp4Path = path.join(CONTENIDO, 'reels', 'mp4', `${r.id}.mp4`);
    if (fs.existsSync(mp4Path)) {
      mediaFiles = [mp4Path];
    } else {
      return res.status(400).json({ error: 'No se encontró el video MP4 compilado para este reel. Compílalo primero.' });
    }
  }

  // Acknowledge request immediately
  res.json({ started: true });

  // Upload and publish in background
  (async () => {
    try {
      broadcast('log', { text: `▶ Iniciando publicación de ${id} a Postiz...\n`, type: 'info' });
      
      const uploadedMedia = [];
      const host = config.postizHost.replace(/\/$/, '');
      const uploadUrl = `${host}/public/v1/upload`;

      for (let i = 0; i < mediaFiles.length; i++) {
        const filePath = mediaFiles[i];
        const fileName = path.basename(filePath);
        broadcast('log', { text: `   Subiendo archivo (${i+1}/${mediaFiles.length}): ${fileName}...\n` });

        const fileBuffer = fs.readFileSync(filePath);
        const blob = new Blob([fileBuffer], { type: isReel ? 'video/mp4' : 'image/png' });
        const form = new FormData();
        form.append('file', blob, fileName);

        const uploadRes = await fetch(uploadUrl, {
          method: 'POST',
          headers: {
            'Authorization': config.postizApiKey
          },
          body: form
        });

        if (!uploadRes.ok) {
          const errText = await uploadRes.text();
          throw new Error(`Fallo al subir ${fileName} a Postiz: ${uploadRes.statusText} (${errText})`);
        }

        const uploadResult = await uploadRes.json();
        uploadedMedia.push({
          id: uploadResult.id,
          path: uploadResult.path
        });
      }

      broadcast('log', { text: `   ✓ ${mediaFiles.length} archivos subidos con éxito.\n`, type: 'success' });
      broadcast('log', { text: `   Enviando publicación a Postiz (Modo: ${mode === 'schedule' ? 'Programado para ' + date : 'Inmediato'})...\n` });

      const postsUrl = `${host}/public/v1/posts`;
      const postBody = {
        type: mode === 'schedule' ? 'schedule' : 'now',
        shortLink: false,
        tags: [],
        posts: [
          {
            integration: {
              id: config.postizChannelId
            },
            value: [
              {
                content: caption,
                image: uploadedMedia
              }
            ],
            settings: {
              __type: "EmptySettings"
            }
          }
        ]
      };

      if (mode === 'schedule') {
        postBody.date = new Date(date).toISOString();
      }

      const postRes = await fetch(postsUrl, {
        method: 'POST',
        headers: {
          'Authorization': config.postizApiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(postBody)
      });

      if (!postRes.ok) {
        const errText = await postRes.text();
        throw new Error(`Fallo al crear la publicación en Postiz: ${postRes.statusText} (${errText})`);
      }

      // Mark as published locally in state
      const state = loadState();
      const prev = state[id] || {};
      state[id] = { ...prev, published: true, publishedAt: new Date().toISOString() };
      saveState(state);

      broadcast('log', { text: `✓ ¡Publicación creada con éxito en Postiz para ${id}!\n`, type: 'success' });
      broadcast('state-update', { id });
      broadcast('action-done', { action: 'postiz-publish', code: 0 });

    } catch (err) {
      broadcast('log', { text: `✗ Error al publicar en Postiz: ${err.message}\n`, type: 'error' });
      broadcast('action-done', { action: 'postiz-publish', code: 1 });
    }
  })();
});

// ── Make.com Integration ───────────────────────────────────────────
app.post('/api/make/publish', async (req, res) => {
  const { id, caption } = req.body;
  const config = loadConfig();

  if (!config.makeWebhookUrl) {
    return res.status(400).json({ error: 'Webhook de Make.com / n8n no configurado. Configúralo en Configuración.' });
  }

  let mediaFiles = [];
  let isReel = !id.startsWith('C');

  if (!isReel) {
    const carousels = loadCarousels();
    const c = carousels.find(x => x.id === id);
    if (!c) return res.status(404).json({ error: 'Carrusel no encontrado' });
    const pngDir = path.join(CONTENIDO, 'carruseles', 'pngs', `${c.id}-${c.file}`);
    if (fs.existsSync(pngDir)) {
      const files = fs.readdirSync(pngDir).filter(f => f.endsWith('.png')).sort();
      mediaFiles = files.map(f => path.join(pngDir, f));
    }
    if (mediaFiles.length === 0) {
      return res.status(400).json({ error: 'No se encontraron PNGs generados para este carrusel. Genéralos primero.' });
    }
  } else {
    const reels = loadReels();
    const r = reels.find(x => x.id === id);
    if (!r) return res.status(404).json({ error: 'Reel no encontrado' });
    const mp4Path = path.join(CONTENIDO, 'reels', 'mp4', `${r.id}.mp4`);
    if (fs.existsSync(mp4Path)) {
      mediaFiles = [mp4Path];
    } else {
      return res.status(400).json({ error: 'No se encontró el video MP4 compilado para este reel. Compílalo primero.' });
    }
  }

  // Acknowledge request immediately
  res.json({ started: true });

  // Upload to Make in background
  (async () => {
    try {
      broadcast('log', { text: `▶ Iniciando envío de ${id} a Make.com / n8n...\n`, type: 'info' });
      
      const form = new FormData();
      form.append('id', id);
      form.append('caption', caption);
      form.append('isReel', isReel ? 'true' : 'false');

      for (let i = 0; i < mediaFiles.length; i++) {
        const filePath = mediaFiles[i];
        const fileName = path.basename(filePath);
        broadcast('log', { text: `   Preparando archivo (${i+1}/${mediaFiles.length}): ${fileName}...\n` });

        const fileBuffer = fs.readFileSync(filePath);
        const blob = new Blob([fileBuffer], { type: isReel ? 'video/mp4' : 'image/png' });
        form.append(`file_${i}`, blob, fileName);
      }

      broadcast('log', { text: `   Enviando payload multipart a Make.com / n8n...\n` });

      const response = await fetch(config.makeWebhookUrl, {
        method: 'POST',
        body: form
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Error en el Webhook de Make / n8n: ${response.statusText} (${errText})`);
      }

      // Mark as published locally in state
      const state = loadState();
      const prev = state[id] || {};
      state[id] = { ...prev, published: true, publishedAt: new Date().toISOString() };
      saveState(state);

      broadcast('log', { text: `✓ ¡Enviado con éxito a Make.com / n8n para ${id}!\n`, type: 'success' });
      broadcast('state-update', { id });
      broadcast('action-done', { action: 'make-publish', code: 0 });

    } catch (err) {
      broadcast('log', { text: `✗ Error al enviar a Make.com / n8n: ${err.message}\n`, type: 'error' });
      broadcast('action-done', { action: 'make-publish', code: 1 });
    }
  })();
});

// ── Render actions ─────────────────────────────────────────────────
let activeProcess = null;

app.post('/api/generate-pngs', (req, res) => {
  if (activeProcess) return res.status(409).json({ error: 'Proceso activo en curso' });
  res.json({ started: true });
  broadcast('log', { text: '▶ Generando PNGs de todos los carruseles...\n', type: 'info' });
  const child = spawn('node', ['generar-pngs.js'], { cwd: path.join(CONTENIDO, 'carruseles') });
  activeProcess = child;
  child.stdout.on('data', d => broadcast('log', { text: d.toString() }));
  child.stderr.on('data', d => broadcast('log', { text: d.toString(), type: 'error' }));
  child.on('close', async code => {
    activeProcess = null;
    broadcast('log', { text: `\n${code===0?'✓':'✗'} Proceso de generación de PNGs finalizado (${code})\n`, type: code===0?'success':'error' });
    
    if (code === 0) {
      broadcast('log', { text: `[R2] Iniciando subida de PNGs a Cloudflare R2...\n`, type: 'info' });
      try {
        const pngDir = path.join(CONTENIDO, 'carruseles', 'pngs');
        if (fs.existsSync(pngDir)) {
          const folders = fs.readdirSync(pngDir).filter(f => fs.statSync(path.join(pngDir, f)).isDirectory());
          let count = 0;
          const state = loadState();
          for (const folder of folders) {
            const folderPath = path.join(pngDir, folder);
            const files = fs.readdirSync(folderPath).filter(f => f.endsWith('.png'));
            const parts = folder.split('-');
            const carouselId = parts[0].toUpperCase();
            
            for (const file of files) {
              const filePath = path.join(folderPath, file);
              const r2Key = `cgm/carruseles/pngs/${folder}/${file}`;
              await uploadFileToR2(filePath, r2Key, 'image/png');
              count++;
            }
            
            state[carouselId] = {
              ...state[carouselId],
              pngCount: files.length
            };
          }
          saveState(state);
          broadcast('log', { text: `[R2] ✓ Se subieron ${count} PNGs con éxito a R2.\n`, type: 'success' });
        }
      } catch (err) {
        broadcast('log', { text: `[R2] ✗ Error subiendo PNGs a R2: ${err.message}\n`, type: 'error' });
      }
    }
    
    broadcast('action-done', { action: 'pngs', code });
  });
});

app.post('/api/render/:id', (req, res) => {
  if (activeProcess) return res.status(409).json({ error: 'Proceso activo en curso' });
  const id = req.params.id.toUpperCase();
  const reels = loadReels();
  const r  = reels.find(x => x.id === id);
  if (!r)  return res.status(404).json({ error: 'Reel no encontrado' });
  res.json({ started: true });
  broadcast('log', { text: `▶ Renderizando ${id} — ${r.title}...\n`, type: 'info' });
  const chromePath = getChromeExecutable().replace(/\\/g, '\\\\');
  const script = `
import{bundle}from'@remotion/bundler';
import{renderMedia,selectComposition}from'@remotion/renderer';
import{createRequire}from'module';
import path from'path';
import{fileURLToPath}from'url';
import fs from'fs';
const __dirname=path.dirname(fileURLToPath(import.meta.url));
const require=createRequire(import.meta.url);
const ffmpegPath=require('ffmpeg-static');
const outDir=path.join(__dirname,'..','mp4');
fs.mkdirSync(outDir,{recursive:true});
const b=await bundle({entryPoint:path.resolve(__dirname,'src/index.jsx'),webpackOverride:c=>c,enableCaching:true});
const comp=await selectComposition({serveUrl:b,id:'${id}',browserExecutable:'${chromePath}'});
await renderMedia({composition:comp,serveUrl:b,codec:'h264',outputLocation:path.join(outDir,'${id}.mp4'),ffmpegPath,browserExecutable:'${chromePath}',puppeteerArgs:['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--disable-gpu'],onProgress:({progress})=>{process.stdout.write('PROGRESS:'+Math.round(progress*100)+'\\n');},chromiumOptions:{disableWebSecurity:true}});
console.log('DONE');`;
  const tmp = path.join(REELS_DIR, `_tmp_${id}.mjs`);
  fs.writeFileSync(tmp, script);
  const child = spawn('node', [`_tmp_${id}.mjs`], { cwd: REELS_DIR });
  activeProcess = child;
  child.stdout.on('data', d => {
    const t = d.toString();
    if (t.startsWith('PROGRESS:')) broadcast('progress', { id, pct: parseInt(t.slice(9)) });
    else broadcast('log', { text: t });
  });
  child.stderr.on('data', d => broadcast('log', { text: d.toString(), type: 'error' }));
  child.on('close', async code => {
    activeProcess = null;
    fs.rmSync(tmp, { force: true });

    if (code === 0) {
      broadcast('log', { text: `[R2] Iniciando subida del Reel renderizado a Cloudflare R2...\n`, type: 'info' });
      const mp4Path = path.join(BASE, 'contenido', 'reels', 'mp4', `${id}.mp4`);
      if (fs.existsSync(mp4Path)) {
        const r2Key = `cgm/reels/mp4/${id}.mp4`;
        const r2Url = await uploadFileToR2(mp4Path, r2Key, 'video/mp4');
        if (r2Url) {
          broadcast('log', { text: `[R2] ✓ Reel subido con éxito a R2: ${r2Url}\n`, type: 'success' });
          const state = loadState();
          state[id] = {
            ...state[id],
            hasVideo: true,
            videoSize: (fs.statSync(mp4Path).size/1024/1024).toFixed(1)
          };
          saveState(state);
        } else {
          broadcast('log', { text: `[R2] ✗ Error al subir el Reel a R2.\n`, type: 'error' });
        }
      }
    }

    broadcast('action-done', { action: 'render', id, code });
    broadcast('log', { text: `\n${code===0?'✓':'✗'} ${id}.mp4\n`, type: code===0?'success':'error' });
  });
});

// ── Start ──────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n◎  Endonautas Content Studio`);
  console.log(`   http://localhost:${PORT}\n`);
  if (!getApiKey()) console.log('   ⚠  API key no configurada — ve a Configuración en la app\n');
});
