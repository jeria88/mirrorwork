#!/usr/bin/env python3
"""
Version B v2 — Carrusel profesional Endonautas
Aplicando patrones de carruseles virales + Canva premium:
  - Diferenciación clara portada / contenido / quote / CTA
  - Contenedores semitransparentes + glass morphism
  - Elementos geométricos decorativos (líneas, arcos, dot grid, anillos)
  - Jerarquía tipográfica definida (96px → 60px → 18px)
  - Numeración ghost como elemento de diseño
  - CTA con energía distinta (overlay jade, botón sólido)
"""

import os, subprocess
from PIL import Image

PEXELS = "/home/nikka/Proyectos/endonautas/brand/social/plantilla/04-fondos-pexels"
LOGO   = "file:///home/nikka/Proyectos/endonautas/brand/social/plantilla/_assets/logo-trans.png"
OUT    = "/home/nikka/Proyectos/endonautas/brand/social/plantilla/05-post-completo/version-b-v2"
BG     = f"file://{PEXELS}/dark-galaxy-3-33931033.jpg"

os.makedirs(OUT, exist_ok=True)

# ─── SHARED CSS ──────────────────────────────────────────────────────────────
FONTS = "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;700;900&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap');"

BASE = """
  * { margin:0; padding:0; box-sizing:border-box; }
  body { width:1080px; height:1080px; background:#000; overflow:hidden; position:relative;
         font-family:'Space Grotesk',system-ui,sans-serif; }

  img.bg {
    position:absolute; inset:0; width:100%; height:100%; object-fit:cover;
    object-position:center center; z-index:0;
  }
  .layer { position:absolute; inset:0; z-index:1; pointer-events:none; }

  /* Header */
  .logo-wrap { display:flex; align-items:center; gap:11px; }
  .logo-img  { width:34px; height:34px; }
  .logo-text {
    font-weight:900; font-size:18px; letter-spacing:-0.02em;
    background:linear-gradient(135deg,#7ecfa8,#7ec8cf);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  }
  .tag {
    font-family:'Plus Jakarta Sans'; font-size:10px; letter-spacing:0.2em;
    color:rgba(240,232,220,0.28); text-transform:uppercase;
    border:1px solid rgba(240,232,220,0.10); border-radius:20px; padding:5px 13px;
  }

  /* Footer nav */
  .nav {
    display:flex; align-items:center; justify-content:space-between;
    border-top:1px solid rgba(255,255,255,0.065); padding-top:20px;
    margin-top:0;
  }
  .swipe {
    font-family:'Plus Jakarta Sans'; font-size:11px; font-weight:500;
    color:rgba(126,207,168,0.60); letter-spacing:0.14em; text-transform:uppercase;
  }
  .slide-info { display:flex; align-items:center; gap:16px; }
  .dots { display:flex; gap:5px; align-items:center; }
  .dot { width:5px; height:5px; border-radius:50%; background:rgba(240,232,220,0.13); }
  .dot.on { background:#7ecfa8; width:20px; border-radius:3px; }
  .num {
    font-family:'Plus Jakarta Sans'; font-size:10px; letter-spacing:0.24em;
    color:rgba(240,232,220,0.20); text-transform:uppercase;
  }

  /* Jade gradient text */
  .jade {
    background:linear-gradient(135deg,#7ecfa8,#7ec8cf);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  }
  em { font-style:italic; }
  em.jade {
    background:linear-gradient(135deg,#7ecfa8,#7ec8cf);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  }
"""

def dots(active, total=4):
    return "".join(f'<div class="dot{"  on" if i==active else ""}"></div>' for i in range(total))

def render(name):
    html = os.path.join(OUT, f"{name}.html")
    png  = os.path.join(OUT, f"{name}.png")
    jpg  = os.path.join(OUT, f"{name}.jpg")
    subprocess.run(["google-chrome","--headless","--disable-gpu",
        f"--screenshot={png}","--window-size=1080,1080","--hide-scrollbars",
        f"file://{html}"], capture_output=True, timeout=30)
    Image.open(png).convert("RGB").save(jpg, "JPEG", quality=92)
    os.remove(png)
    print(f"  ✓ {name}.jpg")

# ═══════════════════════════════════════════════════════════════════════════════
# S1 — PORTADA
# Layout: texto en zona izquierda oscura / estrellas visibles en derecha
# Elementos: gradient text-zone, línea jade vertical, arcos decorativos, ghost "01"
# ═══════════════════════════════════════════════════════════════════════════════
S1 = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
{FONTS}
{BASE}

img.bg {{ filter: brightness(0.58) contrast(1.12) saturate(0.52); }}

/* Zona de texto: gradiente oscuro en left 65%, estrellas visibles en right 35% */
.text-zone {{
  background:
    linear-gradient(to right,
      rgba(0,0,10,0.82) 0%,
      rgba(0,0,10,0.72) 38%,
      rgba(0,0,10,0.45) 58%,
      transparent 78%),
    linear-gradient(to bottom,
      rgba(0,0,0,0.20) 0%, transparent 15%,
      transparent 85%, rgba(0,0,0,0.25) 100%);
}}

/* Vignette de esquinas */
.vig {{
  background: radial-gradient(ellipse 100% 100% at 50% 50%,
    transparent 28%, rgba(0,0,0,0.72) 100%);
}}

/* Ghost número de slide */
.ghost {{
  position:absolute; z-index:2;
  bottom:52px; right:72px;
  font-size:220px; font-weight:900; line-height:1;
  letter-spacing:-0.06em;
  color:rgba(240,232,220,0.042);
  pointer-events:none; user-select:none;
  font-family:'Space Grotesk';
}}

/* Contenido */
.content {{
  position:absolute; inset:0; z-index:10;
  padding:68px 84px 62px;
  display:flex; flex-direction:column; justify-content:space-between;
  color:#F0E8DC;
}}

.top {{ display:flex; align-items:center; justify-content:space-between; }}

.mid {{ flex:1; display:flex; flex-direction:column; justify-content:center; padding:40px 0 20px; }}

.eyebrow {{
  font-family:'Plus Jakarta Sans'; font-size:11px; letter-spacing:0.3em;
  text-transform:uppercase; color:rgba(240,232,220,0.36);
  margin-bottom:24px;
  display:flex; align-items:center; gap:10px;
}}
.eyebrow::before {{
  content:''; display:block; width:24px; height:1.5px;
  background:rgba(126,207,168,0.55); flex-shrink:0;
}}

h1 {{
  font-weight:900; font-size:98px; line-height:0.84;
  letter-spacing:-0.04em; color:#F0E8DC;
  margin-bottom:34px; max-width:580px;
}}

.desc {{
  font-family:'Plus Jakarta Sans'; font-size:18px; line-height:1.65;
  color:rgba(240,232,220,0.40); max-width:440px;
}}
</style></head><body>

<img class="bg" src="{BG}" alt="">

<!-- Zona oscura texto izquierda -->
<div class="layer text-zone"></div>

<!-- Arcos decorativos esquina superior-derecha (SVG) -->
<svg style="position:absolute;inset:0;width:1080px;height:1080px;z-index:5;pointer-events:none;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="vline" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="rgba(126,207,168,0)"/>
      <stop offset="40%"  stop-color="rgba(126,207,168,0.50)"/>
      <stop offset="70%"  stop-color="rgba(126,207,168,0.45)"/>
      <stop offset="100%" stop-color="rgba(126,207,168,0)"/>
    </linearGradient>
  </defs>

  <!-- Arcos concéntricos esquina superior-derecha -->
  <circle cx="1080" cy="0" r="520" fill="none" stroke="rgba(126,207,168,0.065)" stroke-width="1.5"/>
  <circle cx="1080" cy="0" r="448" fill="none" stroke="rgba(126,207,168,0.05)"  stroke-width="1.5"/>
  <circle cx="1080" cy="0" r="376" fill="none" stroke="rgba(126,207,168,0.04)"  stroke-width="1"/>
  <!-- Punto brillante en intersección -->
  <circle cx="1080" cy="520" r="3.5" fill="rgba(126,207,168,0.35)"/>
  <circle cx="560"  cy="0"   r="3"   fill="rgba(126,207,168,0.28)"/>

  <!-- Línea jade vertical en límite text-zone/estrellas (aprox x=660) -->
  <line x1="660" y1="0" x2="660" y2="1080" stroke="url(#vline)" stroke-width="1.5"/>

  <!-- Línea jade decorativa horizontal sobre h1 -->
  <line x1="84" y1="390" x2="240" y2="390" stroke="rgba(126,207,168,0.42)" stroke-width="1.5"/>
</svg>

<!-- Vignette esquinas -->
<div class="layer vig"></div>

<!-- Ghost número -->
<div class="ghost">01</div>

<div class="content">
  <div class="top">
    <div class="logo-wrap">
      <img class="logo-img" src="{LOGO}" alt="">
      <div class="logo-text">Endonautas</div>
    </div>
    <div class="tag">Autoconocimiento</div>
  </div>

  <div class="mid">
    <div class="eyebrow">Vínculos · Patrones</div>
    <h1>La pelea<br>no fue por<br>lo que <em class="jade">dijiste.</em></h1>
    <p class="desc">Fue por lo que eso activó. Y eso tiene un origen que vale la pena encontrar.</p>
  </div>

  <div class="nav">
    <div class="swipe">Desliza para ver →</div>
    <div class="slide-info">
      <div class="dots">{dots(0)}</div>
      <div class="num">01 / 04</div>
    </div>
  </div>
</div>

</body></html>"""

# ═══════════════════════════════════════════════════════════════════════════════
# S2 — LAYOUT / CONTENIDO
# Layout: ghost número grande, franja jade vertical, dot-grid derecha,
#         callout tipo card con borde izquierdo jade
# ═══════════════════════════════════════════════════════════════════════════════
S2 = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
{FONTS}
{BASE}

img.bg {{ filter: brightness(0.55) contrast(1.14) saturate(0.48); }}

.ovr {{
  background:
    rgba(2,4,14,0.48),
    linear-gradient(to bottom, rgba(0,0,0,0.18) 0%, transparent 20%,
                               transparent 80%, rgba(0,0,0,0.22) 100%);
  background: rgba(2,4,14,0.48);
}}

.vig {{
  background: radial-gradient(ellipse 100% 100% at 50% 50%,
    transparent 30%, rgba(0,0,0,0.68) 100%);
}}

/* Dot-grid en lado derecho — textura Canva premium */
.dot-grid {{
  position:absolute; right:0; top:0; bottom:0; width:44%; z-index:4;
  background-image: radial-gradient(rgba(126,207,168,0.16) 1px, transparent 1px);
  background-size:28px 28px;
  -webkit-mask-image: radial-gradient(ellipse 80% 100% at 100% 50%, black 20%, transparent 80%);
  mask-image: radial-gradient(ellipse 80% 100% at 100% 50%, black 20%, transparent 80%);
  pointer-events:none;
}}

/* Ghost número */
.ghost {{
  position:absolute; z-index:3;
  bottom:44px; right:60px;
  font-size:280px; font-weight:900; line-height:1;
  letter-spacing:-0.06em;
  color:rgba(240,232,220,0.048);
  pointer-events:none; user-select:none;
}}

/* Franja jade vertical izquierda */
.v-stripe {{
  position:absolute; z-index:6;
  left:52px; top:22%; bottom:22%;
  width:2.5px;
  background:linear-gradient(to bottom,
    transparent, rgba(126,207,168,0.55) 20%,
    rgba(126,207,168,0.55) 80%, transparent);
}}

.content {{
  position:absolute; inset:0; z-index:10;
  padding:68px 84px 62px;
  display:flex; flex-direction:column; justify-content:space-between;
  color:#F0E8DC;
}}
.top {{ display:flex; align-items:center; justify-content:space-between; }}
.mid {{ flex:1; display:flex; flex-direction:column; justify-content:center; padding:32px 0 16px; }}

/* Label de número de idea */
.idea-label {{
  font-family:'Plus Jakarta Sans'; font-size:11px; letter-spacing:0.28em;
  text-transform:uppercase; color:rgba(126,207,168,0.70);
  margin-bottom:20px;
  display:flex; align-items:center; gap:10px;
}}
.idea-label::before {{
  content:''; display:block; width:18px; height:1.5px;
  background:#7ecfa8;
}}

h2 {{
  font-weight:900; font-size:62px; line-height:0.90;
  letter-spacing:-0.03em; color:#F0E8DC;
  margin-bottom:24px; max-width:560px;
}}

.body {{
  font-family:'Plus Jakarta Sans'; font-size:18px; line-height:1.70;
  color:rgba(240,232,220,0.42); max-width:500px; margin-bottom:0;
}}

/* Callout — card con borde izquierdo jade (Canva premium pattern) */
.callout {{
  margin-top:32px;
  padding:18px 22px;
  border-left:2.5px solid #7ecfa8;
  background:rgba(126,207,168,0.06);
  max-width:500px;
}}
.callout .kw {{
  font-family:'Plus Jakarta Sans'; font-size:10px; letter-spacing:0.22em;
  text-transform:uppercase; color:#7ecfa8; font-weight:600;
  margin-bottom:6px;
}}
.callout .kt {{
  font-family:'Plus Jakarta Sans'; font-size:16px; line-height:1.55;
  color:rgba(240,232,220,0.55);
}}
</style></head><body>

<img class="bg" src="{BG}" alt="">
<div class="layer ovr"></div>
<div class="layer vig"></div>
<div class="dot-grid"></div>
<div class="v-stripe"></div>
<div class="ghost">02</div>

<!-- Línea jade horizontal sobre h2 (SVG) -->
<svg style="position:absolute;inset:0;width:1080px;height:1080px;z-index:8;pointer-events:none;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="hl" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="rgba(126,207,168,0)"/>
      <stop offset="8%"   stop-color="rgba(126,207,168,0.55)"/>
      <stop offset="50%"  stop-color="rgba(126,207,168,0.40)"/>
      <stop offset="100%" stop-color="rgba(126,207,168,0)"/>
    </linearGradient>
  </defs>
  <line x1="84" y1="388" x2="700" y2="388" stroke="url(#hl)" stroke-width="1.5"/>
</svg>

<div class="content">
  <div class="top">
    <div class="logo-wrap">
      <img class="logo-img" src="{LOGO}" alt="">
      <div class="logo-text">Endonautas</div>
    </div>
    <div class="tag">Autoconocimiento</div>
  </div>

  <div class="mid">
    <div class="idea-label">Idea 02</div>
    <h2>No reaccionas<br>a sus <em class="jade">palabras.</em></h2>
    <p class="body">Reaccionas al significado que les das.<br>Y ese significado viene de antes — de algo<br>que se quedó sin resolver.</p>
    <div class="callout">
      <div class="kw">Clave</div>
      <div class="kt">El significado tiene origen. Y ese origen tiene nombre, forma, y fecha.</div>
    </div>
  </div>

  <div class="nav">
    <div class="swipe">Continúa →</div>
    <div class="slide-info">
      <div class="dots">{dots(1)}</div>
      <div class="num">02 / 04</div>
    </div>
  </div>
</div>

</body></html>"""

# ═══════════════════════════════════════════════════════════════════════════════
# S3 — IMPACTO / QUOTE
# Layout: centrado, comilla decorativa jade enorme, líneas horizontales, texto dramático
# Energía distinta: imagen más oscura, foco en la frase
# ═══════════════════════════════════════════════════════════════════════════════
S3 = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
{FONTS}
{BASE}

/* Más oscuro que los otros slides — enfoca el texto */
img.bg {{ filter: brightness(0.40) contrast(1.25) saturate(0.35); }}

.ovr {{ background: rgba(0,0,8,0.55); }}

.vig {{
  background: radial-gradient(ellipse 85% 85% at 50% 50%,
    transparent 22%, rgba(0,0,0,0.78) 100%);
}}

.content {{
  position:absolute; inset:0; z-index:10;
  padding:68px 84px 62px;
  display:flex; flex-direction:column; justify-content:space-between;
  color:#F0E8DC;
}}
.top {{ display:flex; align-items:center; justify-content:space-between; }}

/* Zona de la cita — centrada verticalmente */
.quote-zone {{
  flex:1; display:flex; flex-direction:column; justify-content:center;
  padding:0 0 10px;
}}

/* Comilla decorativa enorme */
.quotemark {{
  font-size:190px; font-weight:900; line-height:0.8;
  color:rgba(126,207,168,0.14);
  margin-bottom:-60px; margin-left:-8px;
  font-family:'Space Grotesk';
  display:block;
}}

.q-line1 {{
  font-weight:300; font-size:52px; line-height:1.1;
  letter-spacing:-0.02em; color:rgba(240,232,220,0.62);
  margin-bottom:8px;
}}

.q-line2 {{
  font-weight:900; font-size:80px; line-height:0.86;
  letter-spacing:-0.04em; color:#F0E8DC;
  margin-bottom:36px;
}}

/* Divisor horizontal jade */
.h-divider {{
  width:100%; height:1px;
  background:linear-gradient(to right,
    rgba(126,207,168,0) 0%,
    rgba(126,207,168,0.45) 20%,
    rgba(126,207,168,0.45) 60%,
    rgba(126,207,168,0) 100%);
  margin-bottom:32px;
}}

.q-sub {{
  font-family:'Plus Jakarta Sans'; font-size:22px; font-weight:400;
  color:rgba(240,232,220,0.42); letter-spacing:-0.01em;
}}
</style></head><body>

<img class="bg" src="{BG}" alt="">
<div class="layer ovr"></div>
<div class="layer vig"></div>

<!-- Líneas horizontales decorativas sobre y bajo el bloque de cita (SVG) -->
<svg style="position:absolute;inset:0;width:1080px;height:1080px;z-index:5;pointer-events:none;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="hl2" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="rgba(126,207,168,0)"/>
      <stop offset="15%"  stop-color="rgba(126,207,168,0.40)"/>
      <stop offset="85%"  stop-color="rgba(126,207,168,0.40)"/>
      <stop offset="100%" stop-color="rgba(126,207,168,0)"/>
    </linearGradient>
  </defs>
  <!-- Línea arriba del bloque de cita -->
  <line x1="0" y1="340" x2="1080" y2="340" stroke="url(#hl2)" stroke-width="1.5"/>
  <!-- Línea abajo del bloque (aproximado) -->
  <line x1="0" y1="840" x2="1080" y2="840" stroke="url(#hl2)" stroke-width="1"/>
</svg>

<div class="content">
  <div class="top">
    <div class="logo-wrap">
      <img class="logo-img" src="{LOGO}" alt="">
      <div class="logo-text">Endonautas</div>
    </div>
  </div>

  <div class="quote-zone">
    <span class="quotemark">❝</span>
    <p class="q-line1">El problema no es</p>
    <h2 class="q-line2">lo que <em class="jade">dijo.</em></h2>
    <div class="h-divider"></div>
    <p class="q-sub">Es lo que eso tocó en ti.</p>
  </div>

  <div class="nav" style="border-top:none; padding-top:0;">
    <div class="swipe">Continúa →</div>
    <div class="slide-info">
      <div class="dots">{dots(2)}</div>
      <div class="num">03 / 04</div>
    </div>
  </div>
</div>

</body></html>"""

# ═══════════════════════════════════════════════════════════════════════════════
# S4 — CTA
# Layout: completamente distinto — overlay jade, centrado, botón sólido prominente,
#         anillo decorativo SVG, energía de acción
# ═══════════════════════════════════════════════════════════════════════════════
S4 = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
{FONTS}
{BASE}

/* Imagen más oscura — el overlay jade toma protagonismo */
img.bg {{ filter: brightness(0.32) contrast(1.20) saturate(0.30); }}

/* Overlay con tint jade — hace que este slide se sienta distinto a todo lo anterior */
.jade-ovr {{
  background:
    rgba(0,18,12,0.68),
    radial-gradient(ellipse 70% 70% at 60% 50%, rgba(20,55,40,0.35) 0%, transparent 70%);
}}

.vig {{
  background: radial-gradient(ellipse 90% 90% at 50% 50%,
    transparent 30%, rgba(0,0,0,0.80) 100%);
}}

.content {{
  position:absolute; inset:0; z-index:10;
  padding:68px 84px 58px;
  display:flex; flex-direction:column; align-items:flex-start;
  justify-content:space-between;
  color:#F0E8DC;
}}
.top {{ width:100%; display:flex; align-items:center; justify-content:space-between; }}

.cta-zone {{
  flex:1; display:flex; flex-direction:column; justify-content:center;
  padding:28px 0 16px;
  max-width:560px;
}}

/* Label con línea jade */
.cta-label {{
  font-family:'Plus Jakarta Sans'; font-size:11px; letter-spacing:0.28em;
  text-transform:uppercase; color:#7ecfa8; font-weight:600;
  margin-bottom:28px;
  display:flex; align-items:center; gap:12px;
}}
.cta-label::before {{
  content:''; display:block; width:24px; height:1.5px; background:#7ecfa8;
}}

.cta-h2 {{
  font-weight:900; font-size:78px; line-height:0.87;
  letter-spacing:-0.038em; color:#F0E8DC;
  margin-bottom:28px;
}}

.cta-desc {{
  font-family:'Plus Jakarta Sans'; font-size:17px; line-height:1.65;
  color:rgba(240,232,220,0.40); margin-bottom:44px; max-width:440px;
}}

/* Botón CTA — sólido jade, texto oscuro, sombra de brillo */
.cta-btn {{
  display:inline-flex; align-items:center; justify-content:center; gap:10px;
  padding:20px 42px; border-radius:60px;
  background:#7ecfa8;
  color:#050e0a;
  font-family:'Plus Jakarta Sans'; font-size:14px; font-weight:700;
  letter-spacing:0.08em; text-transform:uppercase;
  text-decoration:none; width:fit-content;
  box-shadow:0 0 50px rgba(126,207,168,0.30), 0 0 100px rgba(126,207,168,0.12);
}}

.bot-brand {{
  width:100%; display:flex; align-items:center; justify-content:space-between;
}}
.url {{
  font-family:'Plus Jakarta Sans'; font-size:11px; letter-spacing:0.22em;
  color:rgba(240,232,220,0.18); text-transform:uppercase;
}}
</style></head><body>

<img class="bg" src="{BG}" alt="">
<div class="layer jade-ovr"></div>
<div class="layer vig"></div>

<!-- Anillo decorativo — indica "punto de llegada" / acción (SVG) -->
<svg style="position:absolute;inset:0;width:1080px;height:1080px;z-index:5;pointer-events:none;" xmlns="http://www.w3.org/2000/svg">
  <!-- Anillo grande esquina inferior-derecha -->
  <circle cx="1080" cy="1080" r="380" fill="none" stroke="rgba(126,207,168,0.08)" stroke-width="1.5"/>
  <circle cx="1080" cy="1080" r="300" fill="none" stroke="rgba(126,207,168,0.06)" stroke-width="1.5"/>
  <circle cx="1080" cy="1080" r="220" fill="none" stroke="rgba(126,207,168,0.05)" stroke-width="1"/>
  <!-- Punto brillante en borde del anillo -->
  <circle cx="1080" cy="700" r="4" fill="rgba(126,207,168,0.40)"/>
  <circle cx="700"  cy="1080" r="3.5" fill="rgba(126,207,168,0.32)"/>

  <!-- Línea diagonal sutil de la esquina superior-izquierda -->
  <line x1="0" y1="0" x2="380" y2="320" stroke="rgba(126,207,168,0.05)" stroke-width="1"/>
</svg>

<div class="content">
  <div class="top">
    <div class="logo-wrap">
      <img class="logo-img" src="{LOGO}" alt="">
      <div class="logo-text">Endonautas</div>
    </div>
    <div class="tag" style="border-color:rgba(126,207,168,0.20); color:rgba(126,207,168,0.55);">
      Test ECR
    </div>
  </div>

  <div class="cta-zone">
    <div class="cta-label">Mapa interior · Próximo paso</div>
    <div class="cta-h2">Tu mapa interior<br>está <em class="jade">esperando.</em></div>
    <p class="cta-desc">Descubre los patrones que mueven tus vínculos — desde donde se originaron.</p>
    <span class="cta-btn">Comenzar en endonautas.cl &nbsp;→</span>
  </div>

  <div class="bot-brand">
    <div class="url">endonautas.cl</div>
    <div class="slide-info">
      <div class="dots">{dots(3)}</div>
      <div class="num">04 / 04</div>
    </div>
  </div>
</div>

</body></html>"""

# ─── GUARDAR Y RENDERIZAR ────────────────────────────────────────────────────
slides = [("s1-portada", S1), ("s2-layout", S2), ("s3-impacto", S3), ("s4-cta", S4)]

for name, html in slides:
    path = os.path.join(OUT, f"{name}.html")
    with open(path, "w") as f:
        f.write(html)
    render(name)

# Strip de preview
print("\nGenerando preview strip...")
imgs = [Image.open(os.path.join(OUT, f"{n}.jpg")).resize((300,300), Image.LANCZOS) for n,_ in slides]
strip = Image.new("RGB", (len(imgs)*306+6, 312), (8,8,8))
for i, im in enumerate(imgs):
    strip.paste(im, (6+i*306, 6))
strip.save(os.path.join(OUT, "_preview-strip.jpg"), "JPEG", quality=88)
print(f"  ✓ _preview-strip.jpg")
print(f"\n✓ 4 slides profesionales generados en version-b-v2/")
