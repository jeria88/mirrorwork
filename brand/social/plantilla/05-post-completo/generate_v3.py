#!/usr/bin/env python3
"""
generate_v3.py — 3 estilos visuales distintos para carrusel Endonautas
Basado en investigación viral carousels + Canva premium patterns
Formato: 1080×1350 (4:5 portrait — mayor engagement)
"""
import os, subprocess
from pathlib import Path

BASE   = Path("/home/nikka/Proyectos/endonautas/brand/social/plantilla")
PEXELS = BASE / "04-fondos-pexels"
ASSETS = BASE / "_assets"
OUT    = BASE / "05-post-completo"

LOGO   = f"file://{ASSETS}/logo-trans.png"
BG_STARS  = f"file://{PEXELS}/dark-galaxy-3-33931033.jpg"
BG_NEBULA = f"file://{PEXELS}/nebula-space-dark-3-33931036.jpg"

JADE   = "#7ecfa8"
CREAM  = "#F0E8DC"
DARK   = "#05080e"

W, H = 1080, 1350  # 4:5 portrait

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;700;900&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap');"

# ─── SHARED GRAIN OVERLAY ───────────────────────────────────────────────────
GRAIN_SVG = (
    "data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E"
    "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' "
    "numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E"
    "%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"
)

def grain(opacity=0.14):
    return f"""<div style="position:absolute;inset:0;opacity:{opacity};mix-blend-mode:overlay;
pointer-events:none;background-image:url('{GRAIN_SVG}');background-size:256px;z-index:10;"></div>"""

def chrome_render(html_path, jpg_path):
    subprocess.run([
        "google-chrome", "--headless", "--disable-gpu",
        f"--screenshot={jpg_path}",
        f"--window-size={W},{H}",
        "--hide-scrollbars",
        f"--force-device-scale-factor=1",
        f"file://{html_path}"
    ], capture_output=True, check=True)

def make_preview(folder, name, files):
    """Preview horizontal strip"""
    from PIL import Image
    imgs = [Image.open(f) for f in files if Path(f).exists()]
    if not imgs:
        return
    W2 = 340
    H2 = int(H * W2 / W)
    strip_w = W2 * len(imgs) + 8 * (len(imgs) + 1)
    strip = Image.new("RGB", (strip_w, H2 + 16), (8, 10, 18))
    x = 8
    for img in imgs:
        img = img.resize((W2, H2), Image.LANCZOS)
        strip.paste(img, (x, 8))
        x += W2 + 8
    out = folder / f"_preview-{name}.jpg"
    strip.save(str(out), "JPEG", quality=88)
    print(f"  Preview: {out.name}")


# ════════════════════════════════════════════════════════════════════════════
# STYLE A — "EDITORIAL DARK"
# Inspiración: Kinfolk × dark wellness × film photography
# - Grain prominente, glassmorphism callouts, thin rules, tipografía sangría
# ════════════════════════════════════════════════════════════════════════════

def a_shell(bg_url, img_filter, extra_overlay=""):
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
{FONTS}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:{W}px;height:{H}px;overflow:hidden;position:relative;background:{DARK};
  font-family:'Space Grotesk',sans-serif;}}
.bg{{position:absolute;inset:0;background:url('{bg_url}')center/cover;
  filter:{img_filter};}}
.vig{{position:absolute;inset:0;
  background:radial-gradient(ellipse 90% 80% at 50% 50%,transparent 30%,rgba(5,8,14,0.80)100%);}}
em{{font-style:italic;color:{JADE};-webkit-text-fill-color:{JADE};}}
.ui{{position:absolute;inset:0;padding:60px 76px;display:flex;flex-direction:column;
  justify-content:space-between;color:{CREAM};}}
.nav{{display:flex;align-items:center;justify-content:space-between;
  border-bottom:1px solid rgba(240,232,220,0.10);padding-bottom:22px;}}
.lw{{display:flex;align-items:center;gap:10px;}}
.li{{width:28px;height:28px;border-radius:50%;}}
.lt{{font-weight:700;font-size:14px;letter-spacing:0.05em;color:rgba(240,232,220,0.60);}}
.nt{{font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.28em;
  color:rgba(240,232,220,0.22);text-transform:uppercase;}}
.foot{{display:flex;align-items:center;justify-content:space-between;
  border-top:1px solid rgba(240,232,220,0.08);padding-top:22px;}}
.fl{{font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.22em;
  color:rgba(126,207,168,0.55);text-transform:uppercase;}}
.fn{{font-size:11px;letter-spacing:0.18em;color:rgba(240,232,220,0.20);}}
.glass{{background:rgba(240,232,220,0.04);backdrop-filter:blur(12px);
  -webkit-backdrop-filter:blur(12px);border:1px solid rgba(240,232,220,0.08);
  border-radius:3px;padding:20px 24px;}}
.glbl{{font-family:'Plus Jakarta Sans';font-size:9px;letter-spacing:0.35em;
  text-transform:uppercase;color:{JADE};margin-bottom:10px;}}
.glbt{{font-family:'Plus Jakarta Sans';font-size:15px;line-height:1.55;
  color:rgba(240,232,220,0.68);}}
.rule{{width:36px;height:1px;background:{JADE};}}
</style></head><body>
<div class="bg"></div><div class="vig"></div>{extra_overlay}"""

def slide_a1():
    s = a_shell(BG_STARS, "brightness(0.50)contrast(1.22)saturate(0.22)")
    s += grain(0.13)
    s += f"""<div class="ui">
  <div class="nav">
    <div class="lw"><img class="li" src="{LOGO}"><span class="lt">Endonautas</span></div>
    <span class="nt">Vínculos · Patrones</span>
  </div>
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:48px 0 24px;">
    <div class="rule" style="margin-bottom:30px;"></div>
    <h1 style="font-weight:900;font-size:118px;line-height:0.86;letter-spacing:-0.045em;
      color:{CREAM};margin-bottom:44px;">
      La pelea<br>no fue por<br>lo que <em>dijiste.</em>
    </h1>
    <p style="font-family:'Plus Jakarta Sans';font-size:19px;line-height:1.60;
      color:rgba(240,232,220,0.38);max-width:440px;">
      Fue por lo que eso activó.<br>Y eso tiene un origen que vale la pena encontrar.
    </p>
  </div>
  <div class="foot">
    <span class="fl">Desliza para ver →</span>
    <span class="fn">01 / 04</span>
  </div>
</div></body></html>"""
    return s

def slide_a2():
    s = a_shell(BG_STARS, "brightness(0.30)contrast(1.28)saturate(0.18)")
    s += grain(0.15)
    s += f"""<div class="ui">
  <div class="nav">
    <div class="lw"><img class="li" src="{LOGO}"><span class="lt">Endonautas</span></div>
    <span class="nt">Lo que realmente ocurre</span>
  </div>
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:36px;padding:40px 0;">
    <div>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:26px;">
        <div class="rule"></div>
        <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.30em;
          text-transform:uppercase;color:rgba(240,232,220,0.28);">IDEA 01</span>
      </div>
      <h2 style="font-weight:900;font-size:72px;line-height:0.88;letter-spacing:-0.034em;
        color:{CREAM};margin-bottom:28px;">
        No reaccionas<br>a sus <em>palabras.</em>
      </h2>
      <p style="font-family:'Plus Jakarta Sans';font-size:18px;line-height:1.65;
        color:rgba(240,232,220,0.40);max-width:500px;">
        Reaccionas al significado que les das. Y ese significado viene de antes — de algo que se quedó sin resolver.
      </p>
    </div>
    <div class="glass" style="max-width:540px;">
      <div class="glbl">CLAVE</div>
      <div class="glbt">El significado tiene origen. Y ese origen tiene nombre, forma, y fecha.</div>
    </div>
  </div>
  <div class="foot">
    <span class="fl">Continúa →</span><span class="fn">02 / 04</span>
  </div>
</div></body></html>"""
    return s

def slide_a3():
    s = a_shell(BG_STARS, "brightness(0.22)contrast(1.32)saturate(0.14)")
    s += grain(0.16)
    s += f"""<div class="ui" style="justify-content:flex-end;">
  <!-- Nav top absolute -->
  <div style="position:absolute;top:60px;left:76px;right:76px;display:flex;
    align-items:center;justify-content:space-between;
    border-bottom:1px solid rgba(240,232,220,0.08);padding-bottom:22px;">
    <div style="display:flex;align-items:center;gap:10px;">
      <img style="width:28px;height:28px;border-radius:50%;" src="{LOGO}">
      <span style="font-weight:700;font-size:14px;letter-spacing:0.05em;color:rgba(240,232,220,0.45);">Endonautas</span>
    </div>
    <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.28em;
      color:rgba(240,232,220,0.18);text-transform:uppercase;">03 / 04</span>
  </div>

  <!-- Quote centrada verticalmente -->
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;
    padding:120px 0 40px;">
    <div style="font-size:180px;line-height:0.5;color:rgba(126,207,168,0.12);
      font-weight:900;margin-left:-8px;margin-bottom:32px;">&ldquo;</div>
    <p style="font-family:'Plus Jakarta Sans';font-size:52px;font-weight:300;
      line-height:1.08;color:rgba(240,232,220,0.55);letter-spacing:-0.01em;
      margin-bottom:8px;">El problema no es</p>
    <p style="font-size:82px;font-weight:900;line-height:0.92;
      letter-spacing:-0.04em;color:{CREAM};margin-bottom:36px;">
      lo que <em>dijo.</em>
    </p>
    <div style="width:100%;height:1px;
      background:linear-gradient(to right,rgba(126,207,168,0.25),transparent);
      margin-bottom:32px;"></div>
    <p style="font-family:'Plus Jakarta Sans';font-size:22px;line-height:1.5;
      color:rgba(240,232,220,0.32);font-style:italic;">
      Es lo que eso tocó en ti.
    </p>
  </div>

  <div class="foot" style="position:absolute;bottom:60px;left:76px;right:76px;">
    <span class="fl">Continúa →</span><span class="fn">03 / 04</span>
  </div>
</div></body></html>"""
    return s

def slide_a4():
    extra = f"""<div style="position:absolute;inset:0;
      background:radial-gradient(ellipse 80% 60% at 50% 110%,
        rgba(15,70,50,0.45) 0%,transparent 65%);"></div>"""
    s = a_shell(BG_STARS, "brightness(0.26)contrast(1.28)saturate(0.16)", extra)
    s += grain(0.14)
    s += f"""<div class="ui">
  <div class="nav">
    <div class="lw"><img class="li" src="{LOGO}"><span class="lt">Endonautas</span></div>
    <span class="nt">Mapa Interior</span>
  </div>
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:40px 0;">
    <div class="rule" style="margin-bottom:28px;"></div>
    <h2 style="font-weight:900;font-size:100px;line-height:0.86;letter-spacing:-0.04em;
      color:{CREAM};margin-bottom:44px;">
      Tu mapa<br>interior<br>está <em>esperando.</em>
    </h2>
    <p style="font-family:'Plus Jakarta Sans';font-size:18px;line-height:1.65;
      color:rgba(240,232,220,0.38);max-width:430px;margin-bottom:52px;">
      Descubre los patrones que mueven tus vínculos — desde donde se originaron.
    </p>
    <div style="width:fit-content;padding:18px 44px;border-radius:60px;
      background:{JADE};color:#030c07;font-weight:700;font-size:13px;
      letter-spacing:0.14em;text-transform:uppercase;
      box-shadow:0 0 70px rgba(126,207,168,0.38),0 0 140px rgba(126,207,168,0.12);">
      COMENZAR EN ENDONAUTAS.CL →
    </div>
  </div>
  <div class="foot">
    <span style="font-family:'Plus Jakarta Sans';font-size:11px;letter-spacing:0.1em;
      color:rgba(240,232,220,0.18);">endonautas.cl</span>
    <span class="fn">04 / 04</span>
  </div>
</div></body></html>"""
    return s


# ════════════════════════════════════════════════════════════════════════════
# STYLE B — "CANVA PREMIUM DARK"
# Inspiración: plantillas dark Canva Pro, design systems corporate dark
# - Bloques de color opacos, números display grandes, zonas de gradiente
# - Nebula como fondo, efecto color shift
# ════════════════════════════════════════════════════════════════════════════

def b_shell(bg_url, img_filter, extra=""):
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
{FONTS}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:{W}px;height:{H}px;overflow:hidden;position:relative;
  background:#060a12;font-family:'Space Grotesk',sans-serif;}}
.bg{{position:absolute;inset:0;background:url('{bg_url}')center/cover;
  filter:{img_filter};}}
.vig{{position:absolute;inset:0;
  background:linear-gradient(170deg,rgba(6,10,18,0.70)0%,rgba(6,10,18,0.45)50%,rgba(6,10,18,0.80)100%);}}
em{{font-style:italic;color:{JADE};-webkit-text-fill-color:{JADE};}}
</style></head><body>
<div class="bg"></div><div class="vig"></div>{extra}"""

def slide_b1():
    s = b_shell(BG_NEBULA, "brightness(0.42)contrast(1.25)saturate(0.60)hue-rotate(20deg)")
    s += grain(0.12)
    s += f"""
<!-- Barra lateral izquierda jade -->
<div style="position:absolute;left:0;top:0;bottom:0;width:5px;
  background:linear-gradient(to bottom,transparent 5%,{JADE} 30%,{JADE} 70%,transparent 95%);
  opacity:0.6;"></div>

<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:30px;height:30px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:14px;letter-spacing:0.05em;color:rgba(240,232,220,0.65);">Endonautas</span>
  </div>
  <div style="border:1px solid rgba(126,207,168,0.28);border-radius:2px;
    padding:7px 14px;font-family:'Plus Jakarta Sans';font-size:9px;
    letter-spacing:0.28em;text-transform:uppercase;color:rgba(126,207,168,0.6);">
    VÍNCULOS · PATRONES
  </div>
</div>

<!-- Número grande de fondo -->
<div style="position:absolute;right:-20px;bottom:160px;
  font-size:320px;font-weight:900;line-height:1;
  color:rgba(126,207,168,0.04);letter-spacing:-0.06em;
  pointer-events:none;user-select:none;">01</div>

<!-- Contenido -->
<div style="position:absolute;left:64px;right:64px;top:180px;bottom:120px;
  display:flex;flex-direction:column;justify-content:flex-end;">

  <!-- Bloque colored eyebrow -->
  <div style="display:inline-flex;width:fit-content;
    background:rgba(126,207,168,0.10);border-left:3px solid {JADE};
    padding:8px 16px;margin-bottom:28px;">
    <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.30em;
      text-transform:uppercase;color:{JADE};">Post 01 de 09</span>
  </div>

  <h1 style="font-weight:900;font-size:108px;line-height:0.87;letter-spacing:-0.04em;
    color:{CREAM};margin-bottom:40px;">
    La pelea<br>no fue por<br>lo que <em>dijiste.</em>
  </h1>
  <p style="font-family:'Plus Jakarta Sans';font-size:19px;line-height:1.60;
    color:rgba(240,232,220,0.40);max-width:480px;margin-bottom:44px;">
    Fue por lo que eso activó. Y eso tiene un origen que vale la pena encontrar.
  </p>
</div>

<!-- Footer -->
<div style="position:absolute;bottom:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.22em;
    color:rgba(126,207,168,0.55);text-transform:uppercase;">Desliza para ver →</span>
  <span style="font-size:11px;letter-spacing:0.18em;color:rgba(240,232,220,0.20);">01 / 04</span>
</div>
</body></html>"""
    return s

def slide_b2():
    s = b_shell(BG_NEBULA, "brightness(0.28)contrast(1.30)saturate(0.50)hue-rotate(20deg)")
    s += grain(0.13)
    s += f"""
<div style="position:absolute;left:0;top:0;bottom:0;width:5px;
  background:linear-gradient(to bottom,transparent 5%,{JADE} 30%,{JADE} 70%,transparent 95%);opacity:0.6;"></div>

<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:30px;height:30px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:14px;letter-spacing:0.05em;color:rgba(240,232,220,0.55);">Endonautas</span>
  </div>
  <div style="border:1px solid rgba(126,207,168,0.22);border-radius:2px;
    padding:7px 14px;font-family:'Plus Jakarta Sans';font-size:9px;
    letter-spacing:0.28em;text-transform:uppercase;color:rgba(126,207,168,0.45);">
    LO QUE OCURRE
  </div>
</div>

<!-- Número background -->
<div style="position:absolute;right:-20px;bottom:200px;
  font-size:320px;font-weight:900;line-height:1;
  color:rgba(126,207,168,0.04);letter-spacing:-0.06em;">02</div>

<!-- Contenido -->
<div style="position:absolute;left:64px;right:64px;top:180px;">
  <!-- Bloque número display -->
  <div style="display:flex;align-items:center;gap:18px;margin-bottom:30px;">
    <span style="font-size:64px;font-weight:900;color:{JADE};line-height:1;opacity:0.7;">01</span>
    <div style="width:1px;height:60px;background:rgba(126,207,168,0.25);"></div>
    <span style="font-family:'Plus Jakarta Sans';font-size:11px;letter-spacing:0.28em;
      text-transform:uppercase;color:rgba(240,232,220,0.30);">IDEA PRINCIPAL</span>
  </div>

  <h2 style="font-weight:900;font-size:76px;line-height:0.88;letter-spacing:-0.034em;
    color:{CREAM};margin-bottom:30px;">
    No reaccionas<br>a sus <em>palabras.</em>
  </h2>
  <p style="font-family:'Plus Jakarta Sans';font-size:18px;line-height:1.65;
    color:rgba(240,232,220,0.40);max-width:520px;margin-bottom:40px;">
    Reaccionas al significado que les das. Y ese significado viene de antes — de algo que se quedó sin resolver.
  </p>

  <!-- Bloque opaco callout -->
  <div style="background:rgba(126,207,168,0.07);border:1px solid rgba(126,207,168,0.15);
    border-left:3px solid {JADE};border-radius:0 4px 4px 0;padding:20px 24px;max-width:540px;">
    <div style="font-family:'Plus Jakarta Sans';font-size:9px;letter-spacing:0.35em;
      text-transform:uppercase;color:{JADE};margin-bottom:10px;">CLAVE</div>
    <div style="font-family:'Plus Jakarta Sans';font-size:16px;line-height:1.55;
      color:rgba(240,232,220,0.68);">El significado tiene origen. Y ese origen tiene nombre, forma, y fecha.</div>
  </div>
</div>

<div style="position:absolute;bottom:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.22em;
    color:rgba(126,207,168,0.55);text-transform:uppercase;">Continúa →</span>
  <span style="font-size:11px;letter-spacing:0.18em;color:rgba(240,232,220,0.20);">02 / 04</span>
</div>
</body></html>"""
    return s

def slide_b3():
    s = b_shell(BG_NEBULA, "brightness(0.22)contrast(1.32)saturate(0.45)hue-rotate(20deg)")
    s += grain(0.15)
    s += f"""
<!-- Overlay tonal -->
<div style="position:absolute;inset:0;
  background:linear-gradient(to bottom,rgba(6,10,18,0.3) 0%,rgba(6,10,18,0.85) 100%);"></div>

<!-- Líneas horizontales decorativas -->
<svg style="position:absolute;inset:0;width:100%;height:100%;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="hl" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{JADE}" stop-opacity="0"/>
      <stop offset="30%" stop-color="{JADE}" stop-opacity="0.3"/>
      <stop offset="70%" stop-color="{JADE}" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="{JADE}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <line x1="0" y1="420" x2="{W}" y2="420" stroke="url(#hl)" stroke-width="1"/>
  <line x1="0" y1="900" x2="{W}" y2="900" stroke="url(#hl)" stroke-width="1"/>
</svg>

<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:28px;height:28px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:14px;letter-spacing:0.05em;color:rgba(240,232,220,0.45);">Endonautas</span>
  </div>
  <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.28em;
    color:rgba(240,232,220,0.18);text-transform:uppercase;">03 / 04</span>
</div>

<!-- Quote -->
<div style="position:absolute;left:64px;right:64px;top:0;bottom:0;
  display:flex;flex-direction:column;justify-content:center;padding:140px 0 100px;">
  <div style="font-size:200px;line-height:0.5;color:rgba(126,207,168,0.10);
    font-weight:900;margin-left:-10px;margin-bottom:36px;">&ldquo;</div>

  <p style="font-family:'Plus Jakarta Sans';font-size:56px;font-weight:300;
    line-height:1.06;color:rgba(240,232,220,0.52);letter-spacing:-0.01em;margin-bottom:8px;">
    El problema no es
  </p>
  <p style="font-size:88px;font-weight:900;line-height:0.90;
    letter-spacing:-0.042em;color:{CREAM};margin-bottom:44px;">
    lo que <em>dijo.</em>
  </p>

  <div style="width:80px;height:1px;background:{JADE};opacity:0.5;margin-bottom:32px;"></div>

  <p style="font-family:'Plus Jakarta Sans';font-size:22px;line-height:1.55;
    color:rgba(240,232,220,0.30);font-style:italic;">
    Es lo que eso tocó en ti.
  </p>
</div>

<div style="position:absolute;bottom:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.22em;
    color:rgba(126,207,168,0.55);text-transform:uppercase;">Continúa →</span>
  <span style="font-size:11px;letter-spacing:0.18em;color:rgba(240,232,220,0.20);">03 / 04</span>
</div>
</body></html>"""
    return s

def slide_b4():
    extra = f"""<div style="position:absolute;inset:0;
      background:radial-gradient(ellipse 90% 60% at 50% 100%,
        rgba(10,60,45,0.55) 0%,transparent 65%);"></div>"""
    s = b_shell(BG_NEBULA, "brightness(0.24)contrast(1.28)saturate(0.40)hue-rotate(20deg)", extra)
    s += grain(0.13)
    s += f"""
<div style="position:absolute;left:0;top:0;bottom:0;width:5px;
  background:linear-gradient(to bottom,transparent 5%,{JADE} 30%,{JADE} 70%,transparent 95%);opacity:0.6;"></div>

<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:30px;height:30px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:14px;letter-spacing:0.05em;color:rgba(240,232,220,0.60);">Endonautas</span>
  </div>
  <div style="border:1px solid rgba(126,207,168,0.28);border-radius:2px;
    padding:7px 14px;font-family:'Plus Jakarta Sans';font-size:9px;
    letter-spacing:0.28em;text-transform:uppercase;color:rgba(126,207,168,0.6);">
    PRÓXIMO PASO
  </div>
</div>

<!-- Número background -->
<div style="position:absolute;right:-20px;top:80px;
  font-size:320px;font-weight:900;line-height:1;
  color:rgba(126,207,168,0.04);letter-spacing:-0.06em;">04</div>

<div style="position:absolute;left:64px;right:64px;bottom:110px;top:180px;
  display:flex;flex-direction:column;justify-content:flex-end;">
  <div style="display:inline-flex;width:fit-content;
    background:rgba(126,207,168,0.10);border-left:3px solid {JADE};
    padding:8px 16px;margin-bottom:28px;">
    <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.30em;
      text-transform:uppercase;color:{JADE};">Mapa Interior</span>
  </div>

  <h2 style="font-weight:900;font-size:96px;line-height:0.87;letter-spacing:-0.04em;
    color:{CREAM};margin-bottom:40px;">
    Tu mapa<br>interior está<br><em>esperando.</em>
  </h2>
  <p style="font-family:'Plus Jakarta Sans';font-size:18px;line-height:1.65;
    color:rgba(240,232,220,0.38);max-width:440px;margin-bottom:52px;">
    Descubre los patrones que mueven tus vínculos — desde donde se originaron.
  </p>
  <div style="width:fit-content;padding:20px 48px;border-radius:60px;
    background:{JADE};color:#030c07;font-weight:700;font-size:13px;
    letter-spacing:0.14em;text-transform:uppercase;
    box-shadow:0 0 80px rgba(126,207,168,0.40),0 0 160px rgba(126,207,168,0.14);">
    COMENZAR EN ENDONAUTAS.CL →
  </div>
</div>

<div style="position:absolute;bottom:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <span style="font-family:'Plus Jakarta Sans';font-size:11px;letter-spacing:0.1em;
    color:rgba(240,232,220,0.18);">endonautas.cl</span>
  <span style="font-size:11px;letter-spacing:0.18em;color:rgba(240,232,220,0.20);">04 / 04</span>
</div>
</body></html>"""
    return s


# ════════════════════════════════════════════════════════════════════════════
# STYLE C — "BOLD STATEMENT"
# Inspiración: fashion luxury brands, Jacquemus, Byredo — purismo tipográfico
# - Una sola idea visual por slide, escala extrema
# - Casi sin decoración, máximo contraste
# - Estrellas muy oscuras, texto que domina TODO
# ════════════════════════════════════════════════════════════════════════════

def c_shell(extra=""):
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
{FONTS}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:{W}px;height:{H}px;overflow:hidden;position:relative;
  background:#020408;font-family:'Space Grotesk',sans-serif;}}
.bg{{position:absolute;inset:0;
  background:url('{BG_STARS}')center/cover;
  filter:brightness(0.18)contrast(1.40)saturate(0.12);}}
em{{font-style:italic;color:{JADE};-webkit-text-fill-color:{JADE};}}
</style></head><body>
<div class="bg"></div>{extra}"""

def slide_c1():
    s = c_shell()
    s += grain(0.10)
    # Una línea jade horizontal que divide el slide
    s += f"""
<!-- Línea divisoria jade -->
<div style="position:absolute;left:64px;right:64px;top:680px;
  height:1px;background:linear-gradient(to right,{JADE},rgba(126,207,168,0.2));"></div>

<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:28px;height:28px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:14px;letter-spacing:0.05em;color:rgba(240,232,220,0.50);">Endonautas</span>
  </div>
  <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.28em;
    color:rgba(240,232,220,0.20);text-transform:uppercase;">Vínculos · Patrones</span>
</div>

<!-- Headline ENORME -->
<div style="position:absolute;left:64px;right:0;top:160px;">
  <h1 style="font-weight:900;font-size:150px;line-height:0.83;letter-spacing:-0.055em;
    color:{CREAM};">
    La pelea<br>no fue por<br>lo que
  </h1>
  <!-- Jade word que sangra -->
  <h1 style="font-weight:900;font-size:150px;line-height:0.83;letter-spacing:-0.055em;">
    <em>dijiste.</em>
  </h1>
</div>

<!-- Texto pequeño abajo de la línea -->
<div style="position:absolute;left:64px;right:64px;top:712px;">
  <p style="font-family:'Plus Jakarta Sans';font-size:20px;line-height:1.58;
    color:rgba(240,232,220,0.36);max-width:540px;margin-bottom:0;">
    Fue por lo que eso activó. Y eso tiene un origen que vale la pena encontrar.
  </p>
</div>

<!-- Footer -->
<div style="position:absolute;bottom:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.22em;
    color:rgba(126,207,168,0.55);text-transform:uppercase;">Desliza →</span>
  <span style="font-size:11px;letter-spacing:0.18em;color:rgba(240,232,220,0.20);">01 / 04</span>
</div>
</body></html>"""
    return s

def slide_c2():
    s = c_shell()
    s += grain(0.11)
    s += f"""
<!-- Rectángulo jade bloque izquierdo -->
<div style="position:absolute;left:64px;top:160px;width:6px;height:460px;
  background:linear-gradient(to bottom,{JADE},rgba(126,207,168,0.1));"></div>

<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:28px;height:28px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:14px;letter-spacing:0.05em;color:rgba(240,232,220,0.45);">Endonautas</span>
  </div>
  <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.28em;
    color:rgba(240,232,220,0.18);text-transform:uppercase;">02 / 04</span>
</div>

<div style="position:absolute;left:96px;right:64px;top:160px;">
  <!-- Número display -->
  <div style="font-size:16px;font-weight:500;letter-spacing:0.22em;
    color:rgba(126,207,168,0.45);text-transform:uppercase;margin-bottom:32px;
    font-family:'Plus Jakarta Sans';">01 ── IDEA PRINCIPAL</div>

  <h2 style="font-weight:900;font-size:100px;line-height:0.86;letter-spacing:-0.042em;
    color:{CREAM};margin-bottom:44px;">
    No reaccionas<br>a sus<br><em>palabras.</em>
  </h2>

  <p style="font-family:'Plus Jakarta Sans';font-size:19px;line-height:1.62;
    color:rgba(240,232,220,0.38);max-width:520px;margin-bottom:52px;">
    Reaccionas al significado que les das. Y ese significado viene de antes — de algo que se quedó sin resolver.
  </p>

  <!-- Callout sin glass — solo borde -->
  <div style="border:1px solid rgba(126,207,168,0.18);border-left:none;
    padding:20px 24px;padding-left:0;">
    <div style="font-family:'Plus Jakarta Sans';font-size:9px;letter-spacing:0.38em;
      text-transform:uppercase;color:{JADE};opacity:0.7;margin-bottom:10px;">CLAVE</div>
    <div style="font-family:'Plus Jakarta Sans';font-size:16px;line-height:1.55;
      color:rgba(240,232,220,0.55);">El significado tiene origen. Nombre, forma, y fecha.</div>
  </div>
</div>

<div style="position:absolute;bottom:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.22em;
    color:rgba(126,207,168,0.55);text-transform:uppercase;">Continúa →</span>
  <span style="font-size:11px;letter-spacing:0.18em;color:rgba(240,232,220,0.20);">02 / 04</span>
</div>
</body></html>"""
    return s

def slide_c3():
    s = c_shell()
    s += grain(0.12)
    s += f"""
<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:28px;height:28px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:14px;letter-spacing:0.05em;color:rgba(240,232,220,0.40);">Endonautas</span>
  </div>
  <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.28em;
    color:rgba(240,232,220,0.18);text-transform:uppercase;">03 / 04</span>
</div>

<!-- Comilla decorativa tipográfica -->
<div style="position:absolute;left:54px;top:130px;
  font-size:240px;font-weight:900;line-height:1;color:rgba(126,207,168,0.08);">&ldquo;</div>

<!-- Quote dominante centrado verticalmente -->
<div style="position:absolute;left:64px;right:64px;top:0;bottom:0;
  display:flex;flex-direction:column;justify-content:center;padding:140px 0 100px;">

  <p style="font-family:'Plus Jakarta Sans';font-size:60px;font-weight:300;
    line-height:1.04;color:rgba(240,232,220,0.48);letter-spacing:-0.02em;margin-bottom:6px;">
    El problema no es
  </p>
  <p style="font-size:108px;font-weight:900;line-height:0.86;
    letter-spacing:-0.048em;color:{CREAM};margin-bottom:56px;">
    lo que <em>dijo.</em>
  </p>

  <!-- Separador minimalista -->
  <div style="display:flex;align-items:center;gap:16px;margin-bottom:36px;">
    <div style="width:50px;height:1px;background:{JADE};opacity:0.6;"></div>
    <div style="width:6px;height:6px;border-radius:50%;background:{JADE};opacity:0.5;"></div>
  </div>

  <p style="font-family:'Plus Jakarta Sans';font-size:24px;line-height:1.50;
    color:rgba(240,232,220,0.28);font-style:italic;max-width:480px;">
    Es lo que eso tocó en ti.
  </p>
</div>

<div style="position:absolute;bottom:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.22em;
    color:rgba(126,207,168,0.55);text-transform:uppercase;">Continúa →</span>
  <span style="font-size:11px;letter-spacing:0.18em;color:rgba(240,232,220,0.20);">03 / 04</span>
</div>
</body></html>"""
    return s

def slide_c4():
    s = c_shell(f"""<div style="position:absolute;inset:0;
      background:radial-gradient(ellipse 80% 55% at 50% 105%,
        rgba(8,55,40,0.50) 0%,transparent 60%);"></div>""")
    s += grain(0.11)
    s += f"""
<!-- Nav -->
<div style="position:absolute;top:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <img style="width:28px;height:28px;border-radius:50%;" src="{LOGO}">
    <span style="font-weight:700;font-size:14px;letter-spacing:0.05em;color:rgba(240,232,220,0.55);">Endonautas</span>
  </div>
  <span style="font-family:'Plus Jakarta Sans';font-size:10px;letter-spacing:0.28em;
    color:rgba(240,232,220,0.20);text-transform:uppercase;">Mapa Interior</span>
</div>

<!-- Contenido -->
<div style="position:absolute;left:64px;right:64px;top:0;bottom:100px;
  display:flex;flex-direction:column;justify-content:flex-end;">

  <h2 style="font-weight:900;font-size:126px;line-height:0.83;letter-spacing:-0.052em;
    color:{CREAM};margin-bottom:48px;">
    Tu mapa<br>interior está<br><em>esperando.</em>
  </h2>

  <p style="font-family:'Plus Jakarta Sans';font-size:19px;line-height:1.62;
    color:rgba(240,232,220,0.36);max-width:460px;margin-bottom:52px;">
    Descubre los patrones que mueven tus vínculos — desde donde se originaron.
  </p>

  <div style="width:fit-content;padding:20px 48px;border-radius:60px;
    background:{JADE};color:#020c06;font-weight:700;font-size:13px;
    letter-spacing:0.14em;text-transform:uppercase;
    box-shadow:0 0 80px rgba(126,207,168,0.45),0 0 160px rgba(126,207,168,0.15);">
    COMENZAR EN ENDONAUTAS.CL →
  </div>
</div>

<div style="position:absolute;bottom:52px;left:64px;right:64px;
  display:flex;align-items:center;justify-content:space-between;">
  <span style="font-family:'Plus Jakarta Sans';font-size:11px;letter-spacing:0.1em;
    color:rgba(240,232,220,0.18);">endonautas.cl</span>
  <span style="font-size:11px;letter-spacing:0.18em;color:rgba(240,232,220,0.20);">04 / 04</span>
</div>
</body></html>"""
    return s


# ─── MAIN ───────────────────────────────────────────────────────────────────

def render_version(name, slides_dict):
    folder = OUT / f"version-{name}-v3"
    folder.mkdir(parents=True, exist_ok=True)
    jpgs = []
    for slug, html in slides_dict.items():
        html_path = folder / f"{slug}.html"
        jpg_path  = folder / f"{slug}.jpg"
        html_path.write_text(html, encoding="utf-8")
        print(f"  Rendering {slug}...")
        chrome_render(str(html_path), str(jpg_path))
        # chrome produces PNG by default, convert
        png = folder / f"{slug}.png"
        if png.exists():
            from PIL import Image
            img = Image.open(str(png))
            img.save(str(jpg_path), "JPEG", quality=92)
            png.unlink()
        jpgs.append(jpg_path)
    make_preview(folder, name, jpgs)
    print(f"  Version {name} done → {folder}")

if __name__ == "__main__":
    print("═══ generate_v3 — 3 estilos carrusel Endonautas ═══")

    print("\n[A] Editorial Dark")
    render_version("a", {
        "s1-portada": slide_a1(),
        "s2-layout":  slide_a2(),
        "s3-impacto": slide_a3(),
        "s4-cta":     slide_a4(),
    })

    print("\n[B] Canva Premium Dark")
    render_version("b", {
        "s1-portada": slide_b1(),
        "s2-layout":  slide_b2(),
        "s3-impacto": slide_b3(),
        "s4-cta":     slide_b4(),
    })

    print("\n[C] Bold Statement")
    render_version("c", {
        "s1-portada": slide_c1(),
        "s2-layout":  slide_c2(),
        "s3-impacto": slide_c3(),
        "s4-cta":     slide_c4(),
    })

    print("\n✓ Listo. Outputs en 05-post-completo/version-{a,b,c}-v3/")
