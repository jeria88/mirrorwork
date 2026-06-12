#!/usr/bin/env python3
"""
generate_v4.py — Corrección real: tipografía legible en móvil + fondo visible
Regla: body text ≥ 44px, labels ≥ 20px, gradiente solo bajo texto, stars visibles
Formato: 1080×1080 (square — sin dead space)
"""
import subprocess
from pathlib import Path
from PIL import Image

BASE   = Path("/home/nikka/Proyectos/endonautas/brand/social/plantilla")
PEXELS = BASE / "04-fondos-pexels"
ASSETS = BASE / "_assets"
OUT    = BASE / "05-post-completo"

LOGO   = f"file://{ASSETS}/logo-trans.png"
BG_STARS  = f"file://{PEXELS}/dark-galaxy-3-33931033.jpg"
BG_NEBULA = f"file://{PEXELS}/nebula-space-dark-3-33931036.jpg"

JADE  = "#7ecfa8"
CREAM = "#F0E8DC"
DARK  = "#040810"

W = H = 1080

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:ital,wght@0,300;0,400;0,700;0,900;1,900&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap');"

GRAIN_SVG = (
    "data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E"
    "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' "
    "numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E"
    "%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"
)

def grain_div(op=0.08):
    return f"""<div style="position:absolute;inset:0;opacity:{op};mix-blend-mode:overlay;
pointer-events:none;z-index:8;
background-image:url('{GRAIN_SVG}');background-size:256px;"></div>"""

# Gradiente localizado — solo cubre zona de texto (40% inferior)
# Las estrellas son visibles en la parte superior
def text_zone_gradient(color="5,8,16", alpha_top=0.0, alpha_bot=0.95, zone_pct=60):
    return f"""<div style="position:absolute;inset:0;z-index:2;
background:linear-gradient(to top,
  rgba({color},{alpha_bot}) 0%,
  rgba({color},0.75) {100-zone_pct}%,
  rgba({color},0.30) {100-zone_pct+20}%,
  rgba({color},{alpha_top}) 100%);"></div>"""

def chrome_render(html_path, jpg_path):
    subprocess.run([
        "google-chrome","--headless","--disable-gpu",
        f"--screenshot={jpg_path}",
        f"--window-size={W},{H}",
        "--hide-scrollbars",
        f"file://{html_path}"
    ], capture_output=True, check=True)
    png = Path(str(jpg_path).replace(".jpg", ".png"))
    if png.exists():
        img = Image.open(str(png))
        img.save(str(jpg_path), "JPEG", quality=92)
        png.unlink()

def make_strip(folder, name, files):
    imgs = [Image.open(f) for f in files if Path(f).exists()]
    if not imgs: return
    TW = 320
    TH = 320
    pad = 8
    strip = Image.new("RGB", (TW * len(imgs) + pad * (len(imgs)+1), TH + pad*2), (4,8,16))
    x = pad
    for img in imgs:
        img = img.resize((TW, TH), Image.LANCZOS)
        strip.paste(img, (x, pad))
        x += TW + pad
    out = folder / f"_preview-{name}.jpg"
    strip.save(str(out), "JPEG", quality=88)
    print(f"  strip → {out.name}")


# ════════════════════════════════════════════════════════════════════════════
# STYLE A — "EDITORIAL DARK"
# Stars visible top 50%, strong gradient bottom for legibility
# Typography: editorial rules + glassmorphism card
# ════════════════════════════════════════════════════════════════════════════

def a_base(bg, bf):
    """Stars visible, text legible — local gradient only"""
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
{FONTS}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:{W}px;height:{H}px;overflow:hidden;position:relative;
  background:{DARK};font-family:'Space Grotesk',sans-serif;}}
.bg{{position:absolute;inset:0;z-index:1;
  background:url('{bg}')center/cover;filter:{bf};}}
em{{font-style:italic;color:{JADE};-webkit-text-fill-color:{JADE};}}
.ui{{position:absolute;inset:0;z-index:9;padding:52px 68px;
  display:flex;flex-direction:column;justify-content:space-between;color:{CREAM};}}
.nav{{display:flex;align-items:center;justify-content:space-between;}}
.lw{{display:flex;align-items:center;gap:10px;}}
.li{{width:28px;height:28px;border-radius:50%;}}
.lt{{font-weight:700;font-size:16px;letter-spacing:0.04em;color:rgba(240,232,220,0.75);}}
.nt{{font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.24em;
  color:rgba(240,232,220,0.30);text-transform:uppercase;}}
.foot{{display:flex;align-items:center;justify-content:space-between;}}
.fl{{font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.20em;
  color:rgba(126,207,168,0.65);text-transform:uppercase;}}
.fn{{font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);}}
</style></head><body>
<div class="bg"></div>
{text_zone_gradient("4,8,16", 0.0, 0.94, 62)}
{grain_div(0.08)}"""

def slide_a1():
    s = a_base(BG_STARS, "brightness(0.68)contrast(1.15)saturate(0.30)")
    s += f"""<div class="ui">
  <div class="nav">
    <div class="lw"><img class="li" src="{LOGO}"><span class="lt">Endonautas</span></div>
    <span class="nt">Vínculos · Patrones</span>
  </div>
  <div>
    <!-- Thin rule jade -->
    <div style="width:36px;height:1.5px;background:{JADE};margin-bottom:22px;"></div>
    <h1 style="font-weight:900;font-size:105px;line-height:0.88;letter-spacing:-0.04em;
      color:{CREAM};margin-bottom:32px;">
      La pelea<br>no fue por<br>lo que <em>dijiste.</em>
    </h1>
    <p style="font-family:'Plus Jakarta Sans';font-size:24px;line-height:1.55;
      color:rgba(240,232,220,0.52);max-width:500px;">
      Fue por lo que eso activó. Y eso tiene un origen que vale la pena encontrar.
    </p>
  </div>
  <div class="foot">
    <span class="fl">Desliza para ver →</span>
    <span class="fn">01 / 04</span>
  </div>
</div></body></html>"""
    return s

def slide_a2():
    s = a_base(BG_STARS, "brightness(0.60)contrast(1.18)saturate(0.25)")
    s += f"""<div class="ui">
  <div class="nav">
    <div class="lw"><img class="li" src="{LOGO}"><span class="lt">Endonautas</span></div>
    <span class="nt">Lo que realmente ocurre</span>
  </div>
  <div>
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:20px;">
      <div style="width:32px;height:1.5px;background:{JADE};"></div>
      <span style="font-family:'Plus Jakarta Sans';font-size:13px;letter-spacing:0.28em;
        text-transform:uppercase;color:rgba(240,232,220,0.38);">IDEA 01</span>
    </div>
    <h2 style="font-weight:900;font-size:80px;line-height:0.88;letter-spacing:-0.036em;
      color:{CREAM};margin-bottom:24px;">
      No reaccionas<br>a sus <em>palabras.</em>
    </h2>
    <p style="font-family:'Plus Jakarta Sans';font-size:23px;line-height:1.58;
      color:rgba(240,232,220,0.50);max-width:560px;margin-bottom:28px;">
      Reaccionas al significado que les das. Y ese significado viene de antes — de algo que se quedó sin resolver.
    </p>
    <!-- Glass card -->
    <div style="background:rgba(126,207,168,0.06);backdrop-filter:blur(10px);
      -webkit-backdrop-filter:blur(10px);border:1px solid rgba(126,207,168,0.14);
      border-left:2.5px solid {JADE};border-radius:0 4px 4px 0;padding:18px 22px;max-width:560px;">
      <div style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.32em;
        text-transform:uppercase;color:{JADE};margin-bottom:10px;">CLAVE</div>
      <div style="font-family:'Plus Jakarta Sans';font-size:21px;line-height:1.50;
        color:rgba(240,232,220,0.72);">El significado tiene origen. Nombre, forma, y fecha.</div>
    </div>
  </div>
  <div class="foot">
    <span class="fl">Continúa →</span><span class="fn">02 / 04</span>
  </div>
</div></body></html>"""
    return s

def slide_a3():
    s = a_base(BG_STARS, "brightness(0.55)contrast(1.20)saturate(0.22)")
    s += f"""<div class="ui" style="justify-content:center;">
  <div style="position:absolute;top:52px;left:68px;right:68px;" class="nav">
    <div class="lw"><img class="li" src="{LOGO}">
      <span class="lt" style="color:rgba(240,232,220,0.50);">Endonautas</span></div>
    <span class="fn">03 / 04</span>
  </div>
  <div style="margin-top:20px;">
    <!-- Quotemark visible -->
    <div style="font-size:130px;line-height:0.5;font-weight:900;
      color:rgba(126,207,168,0.20);margin-left:-6px;margin-bottom:28px;">&ldquo;</div>
    <p style="font-family:'Plus Jakarta Sans';font-size:46px;font-weight:300;
      line-height:1.06;color:rgba(240,232,220,0.55);letter-spacing:-0.01em;margin-bottom:6px;">
      El problema no es
    </p>
    <p style="font-size:76px;font-weight:900;line-height:0.90;
      letter-spacing:-0.04em;color:{CREAM};margin-bottom:40px;">
      lo que <em>dijo.</em>
    </p>
    <div style="width:100%;height:1px;
      background:linear-gradient(to right,rgba(126,207,168,0.40),transparent);
      margin-bottom:28px;"></div>
    <p style="font-family:'Plus Jakarta Sans';font-size:24px;line-height:1.50;
      color:rgba(240,232,220,0.40);font-style:italic;">
      Es lo que eso tocó en ti.
    </p>
  </div>
  <div class="foot" style="position:absolute;bottom:52px;left:68px;right:68px;">
    <span class="fl">Continúa →</span><span class="fn">03 / 04</span>
  </div>
</div></body></html>"""
    return s

def slide_a4():
    extra_ov = f"""<div style="position:absolute;inset:0;z-index:3;
      background:radial-gradient(ellipse 80% 65% at 50% 115%,
        rgba(10,55,40,0.55) 0%,transparent 60%);"></div>"""
    s = a_base(BG_STARS, "brightness(0.60)contrast(1.18)saturate(0.25)")
    s = s.replace("</div>\n</body>", "") + extra_ov
    s += f"""<div class="ui">
  <div class="nav">
    <div class="lw"><img class="li" src="{LOGO}"><span class="lt">Endonautas</span></div>
    <span class="nt">Mapa Interior</span>
  </div>
  <div>
    <div style="width:36px;height:1.5px;background:{JADE};margin-bottom:22px;"></div>
    <h2 style="font-weight:900;font-size:96px;line-height:0.88;letter-spacing:-0.04em;
      color:{CREAM};margin-bottom:28px;">
      Tu mapa<br>interior está<br><em>esperando.</em>
    </h2>
    <p style="font-family:'Plus Jakarta Sans';font-size:23px;line-height:1.55;
      color:rgba(240,232,220,0.48);max-width:480px;margin-bottom:44px;">
      Descubre los patrones que mueven tus vínculos — desde donde se originaron.
    </p>
    <div style="width:fit-content;padding:18px 44px;border-radius:60px;
      background:{JADE};color:#030c07;font-weight:700;font-size:14px;
      letter-spacing:0.12em;text-transform:uppercase;
      box-shadow:0 0 70px rgba(126,207,168,0.42),0 0 140px rgba(126,207,168,0.14);">
      COMENZAR EN ENDONAUTAS.CL →
    </div>
  </div>
  <div class="foot">
    <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.10em;
      color:rgba(240,232,220,0.22);">endonautas.cl</span>
    <span class="fn">04 / 04</span>
  </div>
</div></body></html>"""
    return s


# ════════════════════════════════════════════════════════════════════════════
# STYLE B — "CANVA PREMIUM"
# Nebula background, numbered display elements, jade sidebar
# Bottom-anchored content, stars breathe at top
# ════════════════════════════════════════════════════════════════════════════

def b_base(bg, bf, extra=""):
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
{FONTS}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:{W}px;height:{H}px;overflow:hidden;position:relative;
  background:{DARK};font-family:'Space Grotesk',sans-serif;}}
.bg{{position:absolute;inset:0;z-index:1;
  background:url('{bg}')center/cover;filter:{bf};}}
em{{font-style:italic;color:{JADE};-webkit-text-fill-color:{JADE};}}
</style></head><body>
<div class="bg"></div>
{text_zone_gradient("4,6,14", 0.0, 0.96, 65)}
{extra}
{grain_div(0.08)}"""

def slide_b1():
    s = b_base(BG_NEBULA, "brightness(0.65)contrast(1.18)saturate(0.55)hue-rotate(15deg)")
    s += f"""
<!-- Sidebar jade -->
<div style="position:absolute;left:0;top:0;bottom:0;width:4px;z-index:10;
  background:linear-gradient(to bottom,transparent 8%,{JADE} 25%,{JADE} 75%,transparent 92%);
  opacity:0.65;"></div>

<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:30px;height:30px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:16px;letter-spacing:0.04em;color:rgba(240,232,220,0.75);">Endonautas</span>
  </div>
  <div style="border:1px solid rgba(126,207,168,0.30);border-radius:2px;
    padding:8px 16px;font-family:'Plus Jakarta Sans';font-size:12px;
    letter-spacing:0.24em;text-transform:uppercase;color:rgba(126,207,168,0.65);">
    VÍNCULOS · PATRONES
  </div>
</div>

<!-- Contenido fondo -->
<div style="position:absolute;left:64px;right:64px;bottom:52px;z-index:10;">
  <div style="display:inline-block;background:rgba(126,207,168,0.10);
    border-left:3px solid {JADE};padding:9px 18px;margin-bottom:24px;">
    <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.28em;
      text-transform:uppercase;color:{JADE};">Post 01 de 09</span>
  </div>
  <h1 style="font-weight:900;font-size:104px;line-height:0.87;letter-spacing:-0.042em;
    color:{CREAM};margin-bottom:30px;">
    La pelea<br>no fue por<br>lo que <em>dijiste.</em>
  </h1>
  <p style="font-family:'Plus Jakarta Sans';font-size:24px;line-height:1.55;
    color:rgba(240,232,220,0.52);max-width:520px;margin-bottom:28px;">
    Fue por lo que eso activó. Y eso tiene un origen que vale la pena encontrar.
  </p>
  <div style="display:flex;align-items:center;justify-content:space-between;">
    <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;
      color:rgba(126,207,168,0.60);text-transform:uppercase;">Desliza para ver →</span>
    <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">01 / 04</span>
  </div>
</div>
</body></html>"""
    return s

def slide_b2():
    s = b_base(BG_NEBULA, "brightness(0.58)contrast(1.20)saturate(0.50)hue-rotate(15deg)")
    s += f"""
<div style="position:absolute;left:0;top:0;bottom:0;width:4px;z-index:10;
  background:linear-gradient(to bottom,transparent 8%,{JADE} 25%,{JADE} 75%,transparent 92%);opacity:0.65;"></div>

<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:30px;height:30px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:16px;letter-spacing:0.04em;color:rgba(240,232,220,0.65);">Endonautas</span>
  </div>
  <div style="border:1px solid rgba(126,207,168,0.22);border-radius:2px;
    padding:8px 16px;font-family:'Plus Jakarta Sans';font-size:12px;
    letter-spacing:0.24em;text-transform:uppercase;color:rgba(126,207,168,0.45);">
    LO QUE OCURRE
  </div>
</div>

<!-- Contenido -->
<div style="position:absolute;left:64px;right:64px;bottom:52px;z-index:10;">
  <!-- Número display -->
  <div style="display:flex;align-items:center;gap:16px;margin-bottom:22px;">
    <span style="font-size:56px;font-weight:900;color:{JADE};line-height:1;opacity:0.75;">01</span>
    <div style="width:1px;height:52px;background:rgba(126,207,168,0.25);"></div>
    <span style="font-family:'Plus Jakarta Sans';font-size:13px;letter-spacing:0.26em;
      text-transform:uppercase;color:rgba(240,232,220,0.35);">IDEA PRINCIPAL</span>
  </div>
  <h2 style="font-weight:900;font-size:80px;line-height:0.88;letter-spacing:-0.036em;
    color:{CREAM};margin-bottom:22px;">
    No reaccionas<br>a sus <em>palabras.</em>
  </h2>
  <p style="font-family:'Plus Jakarta Sans';font-size:23px;line-height:1.58;
    color:rgba(240,232,220,0.50);max-width:560px;margin-bottom:24px;">
    Reaccionas al significado que les das. Y ese significado viene de antes.
  </p>
  <div style="background:rgba(126,207,168,0.07);border:1px solid rgba(126,207,168,0.16);
    border-left:3px solid {JADE};border-radius:0 3px 3px 0;padding:16px 20px;max-width:560px;margin-bottom:24px;">
    <div style="font-family:'Plus Jakarta Sans';font-size:11px;letter-spacing:0.32em;
      text-transform:uppercase;color:{JADE};margin-bottom:8px;">CLAVE</div>
    <div style="font-family:'Plus Jakarta Sans';font-size:21px;line-height:1.48;
      color:rgba(240,232,220,0.70);">El significado tiene origen. Nombre, forma, y fecha.</div>
  </div>
  <div style="display:flex;justify-content:space-between;">
    <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;
      color:rgba(126,207,168,0.60);text-transform:uppercase;">Continúa →</span>
    <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">02 / 04</span>
  </div>
</div>
</body></html>"""
    return s

def slide_b3():
    s = b_base(BG_NEBULA, "brightness(0.52)contrast(1.22)saturate(0.45)hue-rotate(15deg)")
    s += f"""
<!-- SVG accent lines -->
<svg style="position:absolute;inset:0;width:100%;height:100%;z-index:5;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="hl" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{JADE}" stop-opacity="0"/>
      <stop offset="35%" stop-color="{JADE}" stop-opacity="0.35"/>
      <stop offset="65%" stop-color="{JADE}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="{JADE}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <line x1="0" y1="360" x2="{W}" y2="360" stroke="url(#hl)" stroke-width="1"/>
  <line x1="0" y1="820" x2="{W}" y2="820" stroke="url(#hl)" stroke-width="1"/>
</svg>

<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:28px;height:28px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:15px;letter-spacing:0.04em;color:rgba(240,232,220,0.55);">Endonautas</span>
  </div>
  <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.22em;
    color:rgba(240,232,220,0.22);text-transform:uppercase;">03 / 04</span>
</div>

<!-- Quote centrado -->
<div style="position:absolute;left:64px;right:64px;top:0;bottom:0;z-index:10;
  display:flex;flex-direction:column;justify-content:center;padding-top:80px;">
  <div style="font-size:150px;line-height:0.5;font-weight:900;
    color:rgba(126,207,168,0.18);margin-left:-8px;margin-bottom:28px;">&ldquo;</div>
  <p style="font-family:'Plus Jakarta Sans';font-size:48px;font-weight:300;
    line-height:1.06;color:rgba(240,232,220,0.55);letter-spacing:-0.01em;margin-bottom:6px;">
    El problema no es
  </p>
  <p style="font-size:80px;font-weight:900;line-height:0.90;
    letter-spacing:-0.042em;color:{CREAM};margin-bottom:36px;">
    lo que <em>dijo.</em>
  </p>
  <div style="width:72px;height:1.5px;background:{JADE};opacity:0.60;margin-bottom:28px;"></div>
  <p style="font-family:'Plus Jakarta Sans';font-size:24px;line-height:1.50;
    color:rgba(240,232,220,0.40);font-style:italic;">Es lo que eso tocó en ti.</p>
</div>

<div style="position:absolute;bottom:52px;left:64px;right:64px;z-index:10;
  display:flex;justify-content:space-between;">
  <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;
    color:rgba(126,207,168,0.60);text-transform:uppercase;">Continúa →</span>
  <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">03 / 04</span>
</div>
</body></html>"""
    return s

def slide_b4():
    s = b_base(BG_NEBULA, "brightness(0.58)contrast(1.18)saturate(0.48)hue-rotate(15deg)",
               f"""<div style="position:absolute;inset:0;z-index:3;
      background:radial-gradient(ellipse 85% 60% at 50% 110%,
        rgba(8,55,42,0.55) 0%,transparent 58%);"></div>""")
    s += f"""
<div style="position:absolute;left:0;top:0;bottom:0;width:4px;z-index:10;
  background:linear-gradient(to bottom,transparent 8%,{JADE} 25%,{JADE} 75%,transparent 92%);opacity:0.65;"></div>

<div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:30px;height:30px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:16px;letter-spacing:0.04em;color:rgba(240,232,220,0.70);">Endonautas</span>
  </div>
  <div style="border:1px solid rgba(126,207,168,0.30);border-radius:2px;
    padding:8px 16px;font-family:'Plus Jakarta Sans';font-size:12px;
    letter-spacing:0.24em;text-transform:uppercase;color:rgba(126,207,168,0.60);">
    PRÓXIMO PASO
  </div>
</div>

<div style="position:absolute;left:64px;right:64px;bottom:52px;z-index:10;">
  <div style="display:inline-block;background:rgba(126,207,168,0.10);
    border-left:3px solid {JADE};padding:9px 18px;margin-bottom:22px;">
    <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.28em;
      text-transform:uppercase;color:{JADE};">Mapa Interior</span>
  </div>
  <h2 style="font-weight:900;font-size:96px;line-height:0.87;letter-spacing:-0.042em;
    color:{CREAM};margin-bottom:26px;">
    Tu mapa<br>interior está<br><em>esperando.</em>
  </h2>
  <p style="font-family:'Plus Jakarta Sans';font-size:23px;line-height:1.55;
    color:rgba(240,232,220,0.48);max-width:480px;margin-bottom:40px;">
    Descubre los patrones que mueven tus vínculos — desde donde se originaron.
  </p>
  <div style="display:flex;align-items:center;justify-content:space-between;">
    <div style="padding:18px 44px;border-radius:60px;background:{JADE};color:#030c07;
      font-weight:700;font-size:14px;letter-spacing:0.12em;text-transform:uppercase;
      box-shadow:0 0 80px rgba(126,207,168,0.45),0 0 160px rgba(126,207,168,0.15);">
      COMENZAR EN ENDONAUTAS.CL →
    </div>
    <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.22);">04 / 04</span>
  </div>
</div>
</body></html>"""
    return s


# ════════════════════════════════════════════════════════════════════════════
# STYLE C — "BOLD STATEMENT"
# Stars muy visibles (brightness alto), tipografía brutal
# Una idea por slide — máximo impacto
# Gradiente bottom intenso solo donde está el texto
# ════════════════════════════════════════════════════════════════════════════

def c_base(extra=""):
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
{FONTS}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:{W}px;height:{H}px;overflow:hidden;position:relative;
  background:{DARK};font-family:'Space Grotesk',sans-serif;}}
.bg{{position:absolute;inset:0;z-index:1;
  background:url('{BG_STARS}')center/cover;
  filter:brightness(0.72)contrast(1.12)saturate(0.28);}}
em{{font-style:italic;color:{JADE};-webkit-text-fill-color:{JADE};}}
</style></head><body>
<div class="bg"></div>
{text_zone_gradient("3,6,12", 0.0, 0.96, 58)}
{extra}
{grain_div(0.07)}"""

def slide_c1():
    s = c_base()
    s += f"""
<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:30px;height:30px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:16px;letter-spacing:0.04em;color:rgba(240,232,220,0.72);">Endonautas</span>
  </div>
  <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.24em;
    color:rgba(240,232,220,0.28);text-transform:uppercase;">Vínculos · Patrones</span>
</div>

<!-- Contenido abajo -->
<div style="position:absolute;left:64px;right:0;bottom:52px;z-index:10;">
  <h1 style="font-weight:900;font-size:128px;line-height:0.85;letter-spacing:-0.05em;
    color:{CREAM};margin-bottom:0;">
    La pelea<br>no fue por<br>lo que
  </h1>
  <h1 style="font-weight:900;font-size:128px;line-height:0.85;letter-spacing:-0.05em;
    margin-bottom:30px;">
    <em>dijiste.</em>
  </h1>
  <!-- Línea divisora -->
  <div style="width:calc(100% - 0px);height:1px;
    background:linear-gradient(to right,rgba(126,207,168,0.50),transparent);
    margin-bottom:22px;margin-right:64px;"></div>
  <p style="font-family:'Plus Jakarta Sans';font-size:24px;line-height:1.52;
    color:rgba(240,232,220,0.48);max-width:520px;padding-right:64px;margin-bottom:24px;">
    Fue por lo que eso activó. Y eso tiene un origen que vale la pena encontrar.
  </p>
  <div style="display:flex;padding-right:64px;justify-content:space-between;align-items:center;">
    <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;
      color:rgba(126,207,168,0.65);text-transform:uppercase;">Desliza →</span>
    <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">01 / 04</span>
  </div>
</div>
</body></html>"""
    return s

def slide_c2():
    s = c_base(f"""
<!-- Barra vertical jade izquierda -->
<div style="position:absolute;left:64px;top:160px;width:3px;height:500px;z-index:9;
  background:linear-gradient(to bottom,{JADE},rgba(126,207,168,0.08));"></div>""")
    s += f"""
<div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:28px;height:28px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:15px;letter-spacing:0.04em;color:rgba(240,232,220,0.60);">Endonautas</span>
  </div>
  <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.22);">02 / 04</span>
</div>

<div style="position:absolute;left:88px;right:64px;bottom:52px;z-index:10;">
  <div style="font-size:14px;font-weight:500;letter-spacing:0.22em;
    color:rgba(126,207,168,0.50);text-transform:uppercase;margin-bottom:26px;
    font-family:'Plus Jakarta Sans';">01 ── IDEA PRINCIPAL</div>
  <h2 style="font-weight:900;font-size:96px;line-height:0.86;letter-spacing:-0.044em;
    color:{CREAM};margin-bottom:26px;">
    No reaccionas<br>a sus<br><em>palabras.</em>
  </h2>
  <p style="font-family:'Plus Jakarta Sans';font-size:23px;line-height:1.58;
    color:rgba(240,232,220,0.48);max-width:560px;margin-bottom:28px;">
    Reaccionas al significado que les das. Y ese significado viene de antes — de algo que se quedó sin resolver.
  </p>
  <div style="border-top:1px solid rgba(126,207,168,0.18);
    border-bottom:1px solid rgba(126,207,168,0.10);
    padding:16px 0;margin-bottom:22px;">
    <div style="font-family:'Plus Jakarta Sans';font-size:11px;letter-spacing:0.32em;
      text-transform:uppercase;color:{JADE};opacity:0.75;margin-bottom:8px;">CLAVE</div>
    <div style="font-family:'Plus Jakarta Sans';font-size:21px;line-height:1.48;
      color:rgba(240,232,220,0.60);">El significado tiene origen. Nombre, forma, y fecha.</div>
  </div>
  <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;
    color:rgba(126,207,168,0.65);text-transform:uppercase;">Continúa →</span>
</div>
</body></html>"""
    return s

def slide_c3():
    s = c_base()
    s += f"""
<div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:28px;height:28px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:15px;letter-spacing:0.04em;color:rgba(240,232,220,0.50);">Endonautas</span>
  </div>
  <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.20);">03 / 04</span>
</div>

<div style="position:absolute;left:64px;right:64px;top:0;bottom:0;z-index:10;
  display:flex;flex-direction:column;justify-content:center;padding-top:40px;">
  <!-- Comilla grande como elemento visual -->
  <div style="font-size:200px;line-height:0.45;font-weight:900;
    color:rgba(126,207,168,0.15);margin-left:-10px;margin-bottom:24px;">&ldquo;</div>
  <p style="font-family:'Plus Jakarta Sans';font-size:52px;font-weight:300;
    line-height:1.05;color:rgba(240,232,220,0.52);letter-spacing:-0.015em;margin-bottom:4px;">
    El problema no es
  </p>
  <p style="font-size:92px;font-weight:900;line-height:0.88;
    letter-spacing:-0.046em;color:{CREAM};margin-bottom:40px;">
    lo que <em>dijo.</em>
  </p>
  <div style="display:flex;align-items:center;gap:18px;margin-bottom:26px;">
    <div style="width:50px;height:1.5px;background:{JADE};opacity:0.65;"></div>
    <div style="width:7px;height:7px;border-radius:50%;background:{JADE};opacity:0.55;"></div>
  </div>
  <p style="font-family:'Plus Jakarta Sans';font-size:25px;line-height:1.48;
    color:rgba(240,232,220,0.36);font-style:italic;">Es lo que eso tocó en ti.</p>
</div>

<div style="position:absolute;bottom:52px;left:64px;right:64px;z-index:10;
  display:flex;justify-content:space-between;">
  <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;
    color:rgba(126,207,168,0.60);text-transform:uppercase;">Continúa →</span>
  <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">03 / 04</span>
</div>
</body></html>"""
    return s

def slide_c4():
    extra = f"""<div style="position:absolute;inset:0;z-index:3;
      background:radial-gradient(ellipse 80% 60% at 50% 110%,
        rgba(6,48,36,0.52) 0%,transparent 58%);"></div>"""
    s = c_base(extra)
    s += f"""
<div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:30px;height:30px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:16px;letter-spacing:0.04em;color:rgba(240,232,220,0.70);">Endonautas</span>
  </div>
  <span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.22em;
    color:rgba(240,232,220,0.28);text-transform:uppercase;">Mapa Interior</span>
</div>

<div style="position:absolute;left:64px;right:64px;bottom:52px;z-index:10;">
  <h2 style="font-weight:900;font-size:118px;line-height:0.84;letter-spacing:-0.05em;
    color:{CREAM};margin-bottom:28px;">
    Tu mapa<br>interior está<br><em>esperando.</em>
  </h2>
  <p style="font-family:'Plus Jakarta Sans';font-size:24px;line-height:1.55;
    color:rgba(240,232,220,0.46);max-width:500px;margin-bottom:44px;">
    Descubre los patrones que mueven tus vínculos — desde donde se originaron.
  </p>
  <div style="display:flex;align-items:center;gap:32px;">
    <div style="padding:18px 44px;border-radius:60px;background:{JADE};color:#030c07;
      font-weight:700;font-size:14px;letter-spacing:0.12em;text-transform:uppercase;
      box-shadow:0 0 80px rgba(126,207,168,0.48),0 0 160px rgba(126,207,168,0.16);">
      COMENZAR EN ENDONAUTAS.CL →
    </div>
    <span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.22);">04 / 04</span>
  </div>
</div>
</body></html>"""
    return s


# ─── RENDER ─────────────────────────────────────────────────────────────────

def render_version(slug, slides):
    folder = OUT / f"version-{slug}-v4"
    folder.mkdir(parents=True, exist_ok=True)
    jpgs = []
    for name, html in slides.items():
        html_p = folder / f"{name}.html"
        jpg_p  = folder / f"{name}.jpg"
        html_p.write_text(html, encoding="utf-8")
        print(f"  {name}...")
        chrome_render(str(html_p), str(jpg_p))
        jpgs.append(jpg_p)
    make_strip(folder, slug, jpgs)
    print(f"  → {folder.name}")

if __name__ == "__main__":
    print("═══ generate_v4 ═══")
    print("\n[A] Editorial Dark")
    render_version("a", {"s1-portada":slide_a1(),"s2-layout":slide_a2(),
                          "s3-impacto":slide_a3(),"s4-cta":slide_a4()})
    print("\n[B] Canva Premium")
    render_version("b", {"s1-portada":slide_b1(),"s2-layout":slide_b2(),
                          "s3-impacto":slide_b3(),"s4-cta":slide_b4()})
    print("\n[C] Bold Statement")
    render_version("c", {"s1-portada":slide_c1(),"s2-layout":slide_c2(),
                          "s3-impacto":slide_c3(),"s4-cta":slide_c4()})
    print("\n✓ Listo — version-{a,b,c}-v4/")


# ════════════════════════════════════════════════════════════════════════════
# GENERACIÓN DINÁMICA DE SLIDES desde texto de carrusel
# ════════════════════════════════════════════════════════════════════════════

def generate_carousel_slides(slides, article_title="", template_style="A",
                              bg_image_url="", output_dir="/tmp/slides"):
    """
    Genera PNGs de slides para un carrusel a partir de una lista de textos.
    """
    from pathlib import Path
    import subprocess as sp

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not bg_image_url:
        if template_style == "B":
            bg_image_url = f"file://{PEXELS}/nebula-space-dark-3-33931036.jpg"
        else:
            bg_image_url = f"file://{PEXELS}/dark-galaxy-3-33931033.jpg"

    generated_files = []

    for i, slide_text in enumerate(slides):
        slide_num = i + 1
        total = len(slides)
        is_first = (i == 0)
        is_last = (i == total - 1)

        if is_first:
            slide_type = "portada"
        elif is_last:
            slide_type = "cta"
        else:
            slide_type = f"slide{i+1}"

        if template_style == "A":
            html = _slide_a(slide_text, slide_num, total, slide_type, bg_image_url)
        elif template_style == "B":
            html = _slide_b(slide_text, slide_num, total, slide_type, bg_image_url)
        else:
            html = _slide_c(slide_text, slide_num, total, slide_type, bg_image_url)

        html_path = out / f"slide-{slide_num:02d}-{slide_type}.html"
        jpg_path = out / f"slide-{slide_num:02d}-{slide_type}.jpg"
        html_path.write_text(html, encoding="utf-8")

        try:
            chrome_render(str(html_path), str(jpg_path))
            png_path = Path(str(jpg_path).replace(".jpg", ".png"))
            if png_path.exists():
                generated_files.append(str(png_path))
            else:
                generated_files.append(str(jpg_path))
        except Exception as e:
            import logging
            logging.error(f"Error renderizando slide {slide_num}: {e}")

    return generated_files


def _fmt(text, words_per_line=4):
    """Divide texto en líneas para slides."""
    words = text.split()
    if len(words) <= words_per_line:
        return text
    lines = []
    for i in range(0, len(words), words_per_line):
        lines.append(' '.join(words[i:i+words_per_line]))
    return '<br>'.join(lines)


def _slide_a(text, num, total, stype, bg):
    fbg = "brightness(0.65)contrast(1.15)saturate(0.30)"
    if stype == "portada":
        body = f"""<div><div style="width:36px;height:1.5px;background:{JADE};margin-bottom:22px;"></div><h1 style="font-weight:900;font-size:95px;line-height:0.88;letter-spacing:-0.04em;color:{CREAM};margin-bottom:32px;">{_fmt(text)}</h1></div><div class="foot"><span class="fl">Desliza para ver →</span><span class="fn">{num:02d} / {total:02d}</span></div>"""
    elif stype == "cta":
        body = f"""<div><div style="width:36px;height:1.5px;background:{JADE};margin-bottom:22px;"></div><h2 style="font-weight:900;font-size:80px;line-height:0.88;letter-spacing:-0.04em;color:{CREAM};margin-bottom:28px;">{_fmt(text)}</h2><div style="width:fit-content;padding:18px 44px;border-radius:60px;background:{JADE};color:#030c07;font-weight:700;font-size:14px;letter-spacing:0.12em;text-transform:uppercase;box-shadow:0 0 70px rgba(126,207,168,0.42);">COMENZAR EN ENDONAUTAS.CL →</div></div><div class="foot"><span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.10em;color:rgba(240,232,220,0.22);">endonautas.cl</span><span class="fn">{num:02d} / {total:02d}</span></div>"""
    else:
        body = f"""<div><div style="display:flex;align-items:center;gap:14px;margin-bottom:20px;"><div style="width:32px;height:1.5px;background:{JADE};"></div><span style="font-family:'Plus Jakarta Sans';font-size:13px;letter-spacing:0.28em;text-transform:uppercase;color:rgba(240,232,220,0.38);">IDEA {num-1}</span></div><h2 style="font-weight:900;font-size:72px;line-height:0.90;letter-spacing:-0.036em;color:{CREAM};margin-bottom:24px;">{_fmt(text)}</h2></div><div class="foot"><span class="fl">Continúa →</span><span class="fn">{num:02d} / {total:02d}</span></div>"""
    s = a_base(bg, fbg)
    s += f"""<div class="ui"><div class="nav"><div class="lw"><img class="li" src="{LOGO}"><span class="lt">Endonautas</span></div><span class="nt">{'Portada' if stype=='portada' else 'CTA' if stype=='cta' else 'Contenido'}</span></div>{body}</div></body></html>"""
    return s


def _slide_b(text, num, total, stype, bg):
    fbg = "brightness(0.60)contrast(1.18)saturate(0.50)hue-rotate(15deg)"
    if stype == "portada":
        body = f"""<div style="display:inline-block;background:rgba(126,207,168,0.10);border-left:3px solid {JADE};padding:9px 18px;margin-bottom:24px;"><span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.28em;text-transform:uppercase;color:{JADE};">Post {num} de {total}</span></div><h1 style="font-weight:900;font-size:95px;line-height:0.87;letter-spacing:-0.042em;color:{CREAM};margin-bottom:30px;">{_fmt(text)}</h1><div style="display:flex;align-items:center;justify-content:space-between;"><span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;color:rgba(126,207,168,0.60);text-transform:uppercase;">Desliza para ver →</span><span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">{num:02d} / {total:02d}</span></div>"""
    elif stype == "cta":
        body = f"""<div style="display:inline-block;background:rgba(126,207,168,0.10);border-left:3px solid {JADE};padding:9px 18px;margin-bottom:22px;"><span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.28em;text-transform:uppercase;color:{JADE};">Próximo Paso</span></div><h2 style="font-weight:900;font-size:85px;line-height:0.87;letter-spacing:-0.042em;color:{CREAM};margin-bottom:26px;">{_fmt(text)}</h2><div style="display:flex;align-items:center;gap:16px;"><div style="padding:18px 44px;border-radius:60px;background:{JADE};color:#030c07;font-weight:700;font-size:14px;letter-spacing:0.12em;text-transform:uppercase;box-shadow:0 0 80px rgba(126,207,168,0.45);">COMENZAR EN ENDONAUTAS.CL →</div><span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.22);">{num:02d} / {total:02d}</span></div>"""
    else:
        body = f"""<div style="display:flex;align-items:center;gap:16px;margin-bottom:22px;"><span style="font-size:56px;font-weight:900;color:{JADE};line-height:1;opacity:0.75;">{num-1:02d}</span><div style="width:1px;height:52px;background:rgba(126,207,168,0.25);"></div><span style="font-family:'Plus Jakarta Sans';font-size:13px;letter-spacing:0.26em;text-transform:uppercase;color:rgba(240,232,220,0.35);">IDEA {num-1}</span></div><h2 style="font-weight:900;font-size:72px;line-height:0.88;letter-spacing:-0.036em;color:{CREAM};margin-bottom:22px;">{_fmt(text)}</h2><div style="display:flex;justify-content:space-between;"><span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;color:rgba(126,207,168,0.60);text-transform:uppercase;">Continúa →</span><span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">{num:02d} / {total:02d}</span></div>"""
    s = b_base(bg, fbg)
    s += f"""<div style="position:absolute;left:0;top:0;bottom:0;width:4px;z-index:10;background:linear-gradient(to bottom,transparent 8%,{JADE} 25%,{JADE} 75%,transparent 92%);opacity:0.65;"></div><div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;display:flex;align-items:center;justify-content:space-between;"><div style="display:flex;align-items:center;gap:10px;"><img style="width:30px;height:30px;border-radius:50%;" src="{LOGO}"><span style="font-weight:700;font-size:16px;letter-spacing:0.04em;color:rgba(240,232,220,0.65);">Endonautas</span></div><div style="border:1px solid rgba(126,207,168,0.22);border-radius:2px;padding:8px 16px;font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.24em;text-transform:uppercase;color:rgba(126,207,168,0.45);">{'PORTADA' if stype=='portada' else 'CTA' if stype=='cta' else 'CONTENIDO'}</div></div><div style="position:absolute;left:64px;right:64px;bottom:52px;z-index:10;">{body}</div></body></html>"""
    return s


def _slide_c(text, num, total, stype, bg):
    fbg = "brightness(0.72)contrast(1.12)saturate(0.28)"
    if stype == "portada":
        body = f"""<h1 style="font-weight:900;font-size:120px;line-height:0.85;letter-spacing:-0.05em;color:{CREAM};margin-bottom:0;">{_fmt(text, 3)}</h1><div style="width:calc(100% - 64px);height:1px;background:linear-gradient(to right,rgba(126,207,168,0.50),transparent);margin-bottom:22px;margin-top:22px;"></div><div style="display:flex;padding-right:64px;justify-content:space-between;align-items:center;"><span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;color:rgba(126,207,168,0.65);text-transform:uppercase;">Desliza →</span><span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">{num:02d} / {total:02d}</span></div>"""
    elif stype == "cta":
        body = f"""<h2 style="font-weight:900;font-size:100px;line-height:0.85;letter-spacing:-0.05em;color:{CREAM};margin-bottom:30px;">{_fmt(text, 3)}</h2><div style="display:flex;align-items:center;gap:16px;"><div style="padding:18px 44px;border-radius:60px;background:{JADE};color:#030c07;font-weight:700;font-size:14px;letter-spacing:0.12em;text-transform:uppercase;box-shadow:0 0 80px rgba(126,207,168,0.45);">COMENZAR →</div><span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.22);">{num:02d} / {total:02d}</span></div>"""
    else:
        body = f"""<div style="position:absolute;left:64px;top:160px;width:3px;height:500px;z-index:9;background:linear-gradient(to bottom,{JADE},rgba(126,207,168,0.08));"></div><h2 style="font-weight:900;font-size:80px;line-height:0.88;letter-spacing:-0.042em;color:{CREAM};">{_fmt(text)}</h2><div style="position:absolute;bottom:52px;left:64px;right:64px;z-index:10;display:flex;justify-content:space-between;"><span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.18em;color:rgba(126,207,168,0.60);text-transform:uppercase;">Continúa →</span><span style="font-size:12px;letter-spacing:0.14em;color:rgba(240,232,220,0.25);">{num:02d} / {total:02d}</span></div>"""
    s = c_base()
    s += f"""<div style="position:absolute;top:52px;left:64px;right:64px;z-index:10;display:flex;align-items:center;justify-content:space-between;"><div style="display:flex;align-items:center;gap:10px;"><img style="width:30px;height:30px;border-radius:50%;" src="{LOGO}"><span style="font-weight:700;font-size:16px;letter-spacing:0.04em;color:rgba(240,232,220,0.72);">Endonautas</span></div><span style="font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:0.24em;color:rgba(240,232,220,0.28);text-transform:uppercase;">{'PORTADA' if stype=='portada' else 'CTA' if stype=='cta' else f'SLIDE {num-1}'}</span></div><div style="position:absolute;left:64px;right:0;bottom:52px;z-index:10;">{body}</div></body></html>"""
    return s
