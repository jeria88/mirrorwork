#!/usr/bin/env python3
"""
Generador de post completo Endonautas × 3 versiones × 4 slides
Post: "La pelea no fue por lo que dijiste"

Versiones:
  A — Profundo     · Galaxia de Andrómeda + oscuridad extrema + espacio negativo
  B — Estelar      · Campo de estrellas + textura visible + luminosidad media
  C — Vértigo      · Nebulosa teal (hue-rotate) + glow atmosférico + drama

Slides:
  s1 — Portada (hook)
  s2 — Layout: concepto central
  s3 — Impacto: frase de quiebre
  s4 — CTA: llamada a acción
"""

import os, subprocess
from PIL import Image

PEXELS = "/home/nikka/Proyectos/endonautas/brand/social/plantilla/04-fondos-pexels"
LOGO   = "file:///home/nikka/Proyectos/endonautas/brand/social/plantilla/_assets/logo-trans.png"
OUT    = "/home/nikka/Proyectos/endonautas/brand/social/plantilla/05-post-completo"

# ─────────────────────────────────────────────────────────────────────────────
# TEMAS — imagen + tratamiento fotográfico + color system
# ─────────────────────────────────────────────────────────────────────────────
THEMES = [
    dict(
        id="a", folder="version-a", name="Profundo · Andrómeda",
        bg=f"file://{PEXELS}/milky-way-3-34413531.jpg",
        obj_pos="center center",
        filt="brightness(0.48) contrast(1.45) saturate(0.15)",
        ovr="rgba(5,3,14,0.60)",
        vig_color="0,0,0",    vig_alpha=0.82,
        left_dark="rgba(0,0,0,0.54)",
        glow="none",
        # Tipografía: máximo espacio negativo, sensación de vacío cósmico
        h1_size="96px", h1_lh="0.84",
        tag_style="border:1px solid rgba(240,232,220,0.08);",
    ),
    dict(
        id="b", folder="version-b", name="Estelar · Campo de estrellas",
        bg=f"file://{PEXELS}/dark-galaxy-3-33931033.jpg",
        obj_pos="center center",
        filt="brightness(0.60) contrast(1.10) saturate(0.55)",
        ovr="rgba(2,6,20,0.40)",
        vig_color="0,0,0",    vig_alpha=0.68,
        left_dark="rgba(0,0,0,0.40)",
        glow="none",
        h1_size="90px", h1_lh="0.87",
        tag_style="border:1px solid rgba(240,232,220,0.10);",
    ),
    dict(
        id="c", folder="version-c", name="Vértigo · Nebulosa Teal",
        bg=f"file://{PEXELS}/nebula-space-dark-3-33931036.jpg",
        obj_pos="center 40%",
        filt="brightness(0.44) contrast(1.65) saturate(0.90) hue-rotate(148deg)",
        ovr="rgba(0,12,10,0.52)",
        vig_color="0,5,4",    vig_alpha=0.84,
        left_dark="rgba(0,6,4,0.58)",
        # Glow atmosférico de la nebulosa bleeding hacia el texto
        glow="radial-gradient(ellipse 55% 50% at 75% 42%, rgba(40,90,70,0.28) 0%, transparent 70%)",
        h1_size="90px", h1_lh="0.87",
        tag_style="border:1px solid rgba(126,207,168,0.14);",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# CSS BASE — compartido por todos los slides
# ─────────────────────────────────────────────────────────────────────────────
def base_css(t):
    vig_rgba = f"rgba({t['vig_color']},{t['vig_alpha']})"
    glow_bg  = t["glow"] if t["glow"] != "none" else "transparent"
    return f"""
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;700;900&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}

  body {{
    width:1080px; height:1080px;
    background:#000;
    overflow:hidden; position:relative;
    font-family:'Space Grotesk',system-ui,sans-serif;
  }}

  /* ── Capas de imagen ── */
  .bg-wrap {{
    position:absolute; inset:0; z-index:0; overflow:hidden;
  }}
  .bg-img {{
    width:100%; height:100%; object-fit:cover;
    object-position:{t["obj_pos"]};
    filter:{t["filt"]};
  }}
  .ovr {{
    position:absolute; inset:0; z-index:1;
    background:{t["ovr"]};
  }}
  .glow-layer {{
    position:absolute; inset:0; z-index:2;
    background:{glow_bg};
    pointer-events:none;
  }}
  .vig {{
    position:absolute; inset:0; z-index:3;
    background:
      radial-gradient(ellipse 95% 95% at 50% 50%,
        transparent 22%, {vig_rgba} 100%),
      linear-gradient(to right,
        {t["left_dark"]} 0%, transparent 58%),
      linear-gradient(to bottom,
        rgba(0,0,0,0.22) 0%, transparent 18%,
        transparent 80%, rgba(0,0,0,0.28) 100%);
    pointer-events:none;
  }}
  .content {{
    position:absolute; inset:0; z-index:4;
    padding:68px 84px 62px;
    display:flex; flex-direction:column; justify-content:space-between;
    color:#F0E8DC;
  }}

  /* ── Header ── */
  .top {{
    display:flex; align-items:center; justify-content:space-between;
  }}
  .logo-wrap {{ display:flex; align-items:center; gap:11px; }}
  .logo-img  {{ width:34px; height:34px; }}
  .logo-text {{
    font-weight:900; font-size:18px; letter-spacing:-0.02em;
    background:linear-gradient(135deg,#7ecfa8,#7ec8cf);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  }}
  .tag {{
    font-family:'Plus Jakarta Sans'; font-size:10px; letter-spacing:0.2em;
    color:rgba(240,232,220,0.28); text-transform:uppercase;
    {t["tag_style"]} border-radius:20px; padding:5px 13px;
  }}

  /* ── Zona media ── */
  .mid {{
    flex:1; display:flex; flex-direction:column; justify-content:center;
    padding:36px 0 16px;
  }}
  .eyebrow {{
    font-family:'Plus Jakarta Sans'; font-size:11px; letter-spacing:0.3em;
    text-transform:uppercase; color:rgba(240,232,220,0.34);
    margin-bottom:28px;
    display:flex; align-items:center; gap:12px;
  }}
  .eyebrow::before {{
    content:''; display:block; width:24px; height:1px;
    background:rgba(240,232,220,0.18); flex-shrink:0;
  }}
  h1 {{
    font-weight:900; font-size:{t["h1_size"]}; line-height:{t["h1_lh"]};
    letter-spacing:-0.035em; color:#F0E8DC; margin-bottom:36px;
  }}
  h1 em, h2 em {{
    font-style:italic;
    background:linear-gradient(135deg,#7ecfa8,#7ec8cf);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  }}
  .desc {{
    font-family:'Plus Jakarta Sans'; font-size:17px; line-height:1.65;
    color:rgba(240,232,220,0.38); max-width:490px;
  }}

  /* ── Pie de slide ── */
  .bot {{
    display:flex; align-items:center; justify-content:space-between;
    border-top:1px solid rgba(255,255,255,0.065); padding-top:20px;
  }}
  .swipe {{
    font-family:'Plus Jakarta Sans'; font-size:11px; font-weight:500;
    color:rgba(126,207,168,0.60); letter-spacing:0.14em; text-transform:uppercase;
  }}
  .slide-info {{ display:flex; align-items:center; gap:16px; }}
  .dots {{ display:flex; gap:5px; align-items:center; }}
  .dot {{ width:5px; height:5px; border-radius:50%; background:rgba(240,232,220,0.13); }}
  .dot.on {{ background:#7ecfa8; width:20px; border-radius:3px; }}
  .num {{
    font-family:'Plus Jakarta Sans'; font-size:10px; letter-spacing:0.24em;
    color:rgba(240,232,220,0.20); text-transform:uppercase;
  }}

  /* ── Layout slide ── */
  .slide-num-bg {{
    font-weight:900; font-size:160px; line-height:1;
    letter-spacing:-0.04em; color:rgba(240,232,220,0.055);
    margin-bottom:-28px; margin-left:-6px;
    font-variant-numeric:tabular-nums;
  }}
  h2 {{
    font-weight:900; font-size:62px; line-height:0.90;
    letter-spacing:-0.028em; color:#F0E8DC;
    margin-bottom:28px; max-width:580px;
  }}
  .body {{
    font-family:'Plus Jakarta Sans'; font-size:18px; line-height:1.68;
    color:rgba(240,232,220,0.40); max-width:520px;
  }}

  /* ── Quote slide ── */
  .quote-wrap {{
    flex:1; display:flex; flex-direction:column; justify-content:center;
    padding:40px 0;
  }}
  .q-line1 {{
    font-weight:300; font-size:52px; line-height:1.1;
    letter-spacing:-0.02em; color:rgba(240,232,220,0.65);
    margin-bottom:4px;
  }}
  .q-line2 {{
    font-weight:900; font-size:76px; line-height:0.88;
    letter-spacing:-0.04em; color:#F0E8DC;
    margin-bottom:40px;
  }}
  .q-line2 em {{
    font-style:italic;
    background:linear-gradient(135deg,#7ecfa8,#7ec8cf);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  }}
  .q-sub {{
    font-family:'Plus Jakarta Sans'; font-size:20px; font-weight:500;
    color:rgba(240,232,220,0.42); letter-spacing:-0.01em;
    padding-left:3px;
  }}

  /* ── CTA slide ── */
  .cta-wrap {{
    flex:1; display:flex; flex-direction:column; justify-content:center;
    padding:32px 0 24px;
  }}
  .cta-label {{
    font-family:'Plus Jakarta Sans'; font-size:11px; letter-spacing:0.3em;
    text-transform:uppercase; color:#7ecfa8; margin-bottom:28px;
    display:flex; align-items:center; gap:10px;
  }}
  .cta-label::before {{
    content:''; display:block; width:24px; height:1px;
    background:rgba(126,207,168,0.5);
  }}
  .cta-h2 {{
    font-weight:900; font-size:74px; line-height:0.88;
    letter-spacing:-0.035em; color:#F0E8DC; margin-bottom:28px;
  }}
  .cta-h2 em {{
    font-style:italic;
    background:linear-gradient(135deg,#7ecfa8,#7ec8cf);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  }}
  .cta-desc {{
    font-family:'Plus Jakarta Sans'; font-size:17px; line-height:1.6;
    color:rgba(240,232,220,0.38); max-width:440px; margin-bottom:44px;
  }}
  .cta-btn {{
    display:inline-flex; align-items:center; gap:12px;
    padding:18px 34px; border-radius:40px;
    border:1.5px solid rgba(126,207,168,0.55);
    background:rgba(126,207,168,0.08);
    color:#7ecfa8; font-family:'Plus Jakarta Sans';
    font-size:13px; font-weight:600; letter-spacing:0.1em; text-transform:uppercase;
    text-decoration:none; width:fit-content;
  }}
  .cta-footer {{
    font-family:'Plus Jakarta Sans'; font-size:11px; letter-spacing:0.22em;
    color:rgba(240,232,220,0.18); text-transform:uppercase;
  }}
"""


# ─────────────────────────────────────────────────────────────────────────────
# DOTS helper
# ─────────────────────────────────────────────────────────────────────────────
def dots_html(active, total=4):
    d = ""
    for i in range(total):
        cls = "dot on" if i == active else "dot"
        d += f'<div class="{cls}"></div>'
    return d


# ─────────────────────────────────────────────────────────────────────────────
# SHELL de HTML — imagen + overlays + contenido
# ─────────────────────────────────────────────────────────────────────────────
def html_wrap(t, css_extra, content_html):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
{base_css(t)}
{css_extra}
</style>
</head>
<body>
  <div class="bg-wrap">
    <img class="bg-img" src="{t['bg']}" alt="">
  </div>
  <div class="ovr"></div>
  <div class="glow-layer"></div>
  <div class="vig"></div>
  <div class="content">
    {content_html}
  </div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# GENERADORES por tipo de slide
# ─────────────────────────────────────────────────────────────────────────────
def slide_portada(t):
    content = f"""
    <div class="top">
      <div class="logo-wrap">
        <img class="logo-img" src="{LOGO}" alt="">
        <div class="logo-text">Endonautas</div>
      </div>
      <div class="tag">Autoconocimiento</div>
    </div>
    <div class="mid">
      <div class="eyebrow">Vínculos · Patrones</div>
      <h1>La pelea<br>no fue por<br>lo que <em>dijiste.</em></h1>
      <p class="desc">Fue por lo que eso activó. Y eso tiene un origen que vale la pena encontrar.</p>
    </div>
    <div class="bot">
      <div class="swipe">Desliza para ver →</div>
      <div class="slide-info">
        <div class="dots">{dots_html(0)}</div>
        <div class="num">01 / 04</div>
      </div>
    </div>"""
    return html_wrap(t, "", content)


def slide_layout(t):
    content = f"""
    <div class="top">
      <div class="logo-wrap">
        <img class="logo-img" src="{LOGO}" alt="">
        <div class="logo-text">Endonautas</div>
      </div>
      <div class="tag">Autoconocimiento</div>
    </div>
    <div class="mid">
      <div class="slide-num-bg">02</div>
      <h2>No reaccionas<br>a sus <em>palabras.</em></h2>
      <p class="body">Reaccionas al significado que les das.<br>
      Y ese significado viene de antes — de algo que se quedó sin resolver.</p>
    </div>
    <div class="bot">
      <div class="swipe">Continúa →</div>
      <div class="slide-info">
        <div class="dots">{dots_html(1)}</div>
        <div class="num">02 / 04</div>
      </div>
    </div>"""
    return html_wrap(t, "", content)


def slide_quote(t):
    content = f"""
    <div class="top">
      <div class="logo-wrap">
        <img class="logo-img" src="{LOGO}" alt="">
        <div class="logo-text">Endonautas</div>
      </div>
      <div class="tag">Autoconocimiento</div>
    </div>
    <div class="quote-wrap">
      <div class="q-line1">El problema no es</div>
      <div class="q-line2">lo que <em>dijo.</em></div>
      <div class="q-sub">Es lo que eso tocó en ti.</div>
    </div>
    <div class="bot">
      <div class="swipe">Continúa →</div>
      <div class="slide-info">
        <div class="dots">{dots_html(2)}</div>
        <div class="num">03 / 04</div>
      </div>
    </div>"""
    return html_wrap(t, "", content)


def slide_cta(t):
    content = f"""
    <div class="top">
      <div class="logo-wrap">
        <img class="logo-img" src="{LOGO}" alt="">
        <div class="logo-text">Endonautas</div>
      </div>
    </div>
    <div class="cta-wrap">
      <div class="cta-label">Test ECR · Mapa interior</div>
      <div class="cta-h2">Tu mapa interior<br>está <em>esperando.</em></div>
      <p class="cta-desc">Descubre los patrones que mueven tus vínculos — desde la raíz.</p>
      <span class="cta-btn">Comenzar en endonautas.cl &nbsp;→</span>
    </div>
    <div class="bot" style="border:none; padding-top:0;">
      <div class="cta-footer">endonautas.cl</div>
      <div class="slide-info">
        <div class="dots">{dots_html(3)}</div>
        <div class="num">04 / 04</div>
      </div>
    </div>"""
    return html_wrap(t, "", content)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — generar + renderizar
# ─────────────────────────────────────────────────────────────────────────────
SLIDE_FUNCS = [
    ("s1-portada", slide_portada),
    ("s2-layout",  slide_layout),
    ("s3-impacto", slide_quote),
    ("s4-cta",     slide_cta),
]

def render(html_path, jpg_path):
    png_path = jpg_path.replace(".jpg", ".png")
    subprocess.run([
        "google-chrome", "--headless", "--disable-gpu",
        f"--screenshot={png_path}",
        "--window-size=1080,1080", "--hide-scrollbars",
        f"file://{html_path}"
    ], capture_output=True, timeout=30)
    img = Image.open(png_path).convert("RGB")
    img.save(jpg_path, "JPEG", quality=92)
    os.remove(png_path)
    print(f"  ✓ {os.path.basename(jpg_path)}")

generated = []
for t in THEMES:
    folder = os.path.join(OUT, t["folder"])
    os.makedirs(folder, exist_ok=True)
    print(f"\n── {t['name']} ──")
    for slug, fn in SLIDE_FUNCS:
        html_path = os.path.join(folder, f"{slug}.html")
        jpg_path  = os.path.join(folder, f"{slug}.jpg")
        html = fn(t)
        with open(html_path, "w") as f:
            f.write(html)
        render(html_path, jpg_path)
        generated.append(jpg_path)

# ── Preview strips por versión ──
print("\nCreando preview strips...")
for t in THEMES:
    folder = os.path.join(OUT, t["folder"])
    jpgs   = [os.path.join(folder, f"{s}.jpg") for s, _ in SLIDE_FUNCS]
    N      = len(jpgs)
    W_THUMB = 300; H_THUMB = 300; PAD = 6
    strip = Image.new("RGB", (N*(W_THUMB+PAD)+PAD, H_THUMB+PAD*2), (8,8,8))
    for i, jp in enumerate(jpgs):
        img = Image.open(jp).resize((W_THUMB, H_THUMB), Image.LANCZOS)
        strip.paste(img, (PAD + i*(W_THUMB+PAD), PAD))
    strip_path = os.path.join(folder, "_preview-strip.jpg")
    strip.save(strip_path, "JPEG", quality=88)
    print(f"  ✓ {t['folder']}/_preview-strip.jpg")

print(f"\n✓ {len(generated)} slides generados")
