"""
Layouts de slides para carruseles Endonautas.
Cada layout es una función que recibe datos y devuelve HTML.
"""

LAYOUTS = {
    "portada": {
        "name": "Portada",
        "desc": "Título impactante + fondo + logo",
        "fields": ["title", "subtitle", "body", "cta_text"],
    },
    "split": {
        "name": "Split",
        "desc": "Texto izquierda / Imagen derecha",
        "fields": ["tag", "title", "body", "image_url"],
    },
    "hero": {
        "name": "Hero",
        "desc": "Imagen fondo completo + texto superpuesto",
        "fields": ["tag", "title", "body", "image_url"],
    },
    "quote": {
        "name": "Quote",
        "desc": "Cita centrada + fondo",
        "fields": ["quote", "author", "image_url"],
    },
    "cta": {
        "name": "CTA Final",
        "desc": "Llamada a acción + botón + logo",
        "fields": ["title", "body", "cta_text", "cta_url"],
    },
    "lista": {
        "name": "Lista",
        "desc": "Lista de puntos + imagen lateral",
        "fields": ["tag", "title", "points", "image_url"],
    },
    "dato": {
        "name": "Dato",
        "desc": "Un dato/frase impactante + fondo",
        "fields": ["dato", "contexto", "image_url"],
    },
    "blur": {
        "name": "Blur Card",
        "desc": "Tarjeta glassmorphism + fondo",
        "fields": ["tag", "title", "body", "image_url"],
    },
}


def get_layouts_json():
    """Devuelve los layouts como JSON para el frontend."""
    import json
    return json.dumps(LAYOUTS, ensure_ascii=False)


def render_slide_html(layout_id, data, slide_num, total, bg_url=None):
    """
    Renderiza el HTML de una slide según el layout.

    Args:
        layout_id: ID del layout (portada, split, hero, etc.)
        data: Dict con los datos de la slide
        slide_num: Número de slide (1-based)
        total: Total de slides
        bg_url: URL de imagen de fondo (opcional)

    Returns:
        HTML completo de la slide
    """
    layout_fn = globals().get(f"_render_{layout_id}", _render_portada)
    return layout_fn(data, slide_num, total, bg_url)


def _render_portada(data, num, total, bg_url):
    title = data.get("title", "Título")
    subtitle = data.get("subtitle", "")
    body = data.get("body", "")
    cta = data.get("cta_text", "Deslizá →")
    bg = bg_url or ""

    bg_style = f"background:url('{bg}')center/cover no-repeat;filter:saturate(1.3)contrast(1.2);opacity:0.5;" if bg else "background:#000;"

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;900&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#0a0a0f;color:#F0E8DC;font-family:'Plus Jakarta Sans',sans-serif;}}
.slide{{width:1080px;height:1350px;display:flex;flex-direction:column;position:relative;overflow:hidden;}}
.label{{font-size:14px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;padding:12px 18px;background:rgba(0,0,0,0.6);position:absolute;top:0;left:0;z-index:10;border-radius:0 0 12px 0;}}
.bg{{position:absolute;inset:0;z-index:1;{bg_style}}}
.dim{{position:absolute;inset:0;z-index:2;background:radial-gradient(ellipse at center,transparent 30%,rgba(0,0,0,0.6) 100%),linear-gradient(180deg,rgba(0,0,0,0.2) 0%,rgba(0,0,0,0.8) 100%);}}
.z1{{position:relative;z-index:3;}}
.shadow{{text-shadow:0 3px 30px rgba(0,0,0,0.8);}}
.glow{{text-shadow:0 0 60px rgba(126,207,168,0.3),0 3px 30px rgba(0,0,0,0.8);}}
.s1{{align-items:center;justify-content:center;text-align:center;padding:80px;}}
.s1 .logo{{display:flex;align-items:center;justify-content:center;gap:14px;margin-bottom:40px;}}
.s1 .logo span{{font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:600;letter-spacing:5px;text-transform:uppercase;color:#7ecfa8;}}
.s1 .title{{font-family:'Space Grotesk',sans-serif;font-size:82px;font-weight:700;line-height:1.1;color:#F0E8DC;margin-bottom:30px;}}
.s1 .title em{{font-style:italic;color:#7ecfa8;}}
.s1 .line{{width:60px;height:2px;background:rgba(126,207,168,0.5);margin:0 auto 30px;}}
.s1 .body{{font-size:28px;font-weight:300;line-height:1.7;color:rgba(240,232,220,0.75);max-width:780px;}}
.s1 .cta{{font-size:16px;font-weight:500;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;margin-top:40px;}}
</style></head><body>
<div class="slide s1">
  <div class="bg"></div>
  <div class="dim"></div>
  <div class="label">{num} — Portada</div>
  <div class="logo z1"><span>Endonautas</span></div>
  <div class="title shadow z1">{title}</div>
  <div class="line z1"></div>
  <div class="body shadow z1">{body}</div>
  <div class="cta z1">{cta}</div>
</div></body></html>"""


def _render_split(data, num, total, bg_url):
    tag = data.get("tag", "IDEA")
    title = data.get("title", "Título")
    body = data.get("body", "Contenido")
    img = data.get("image_url", "")
    bg = bg_url or ""

    img_html = f'<img src="{img}" style="width:100%;height:100%;object-fit:cover;">' if img else ''
    bg_style = f"background:url('{bg}')center/cover no-repeat;opacity:0.15;" if bg else ""

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;900&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#0a0a0f;color:#F0E8DC;font-family:'Plus Jakarta Sans',sans-serif;}}
.slide{{width:1080px;height:1350px;display:flex;flex-direction:column;position:relative;overflow:hidden;}}
.label{{font-size:14px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;padding:12px 18px;background:rgba(0,0,0,0.6);position:absolute;top:0;left:0;z-index:10;border-radius:0 0 12px 0;}}
.bg{{position:absolute;inset:0;z-index:1;{bg_style}}}
.z1{{position:relative;z-index:3;}}
.shadow{{text-shadow:0 3px 30px rgba(0,0,0,0.8);}}
.s2{{background:#0a0a0f;}}
.s2 .grid2{{display:grid;grid-template-columns:1fr 1fr;width:100%;height:100%;}}
.s2 .texto{{display:flex;flex-direction:column;justify-content:center;padding:80px;}}
.s2 .tag{{font-size:14px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;margin-bottom:28px;}}
.s2 .title{{font-family:'Space Grotesk',sans-serif;font-size:64px;font-weight:700;line-height:1.15;margin-bottom:28px;}}
.s2 .title em{{font-style:italic;color:#7ecfa8;}}
.s2 .body{{font-size:26px;font-weight:300;line-height:1.7;color:rgba(240,232,220,0.55);}}
.s2 .img-wrap{{position:relative;}}
.s2 .img-wrap .fade{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(10,10,15,0.6) 0%,transparent 40%);}}
</style></head><body>
<div class="slide s2">
  <div class="bg"></div>
  <div class="label">{num} — Split</div>
  <div class="grid2 z1">
    <div class="texto">
      <div class="tag">{tag}</div>
      <div class="title shadow">{title}</div>
      <div class="body shadow">{body}</div>
    </div>
    <div class="img-wrap">
      {img_html}
      <div class="fade"></div>
    </div>
  </div>
</div></body></html>"""


def _render_hero(data, num, total, bg_url):
    tag = data.get("tag", "")
    title = data.get("title", "Título")
    body = data.get("body", "")
    img = data.get("image_url", bg_url or "")

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;900&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#000;color:#F0E8DC;font-family:'Plus Jakarta Sans',sans-serif;}}
.slide{{width:1080px;height:1350px;display:flex;flex-direction:column;position:relative;overflow:hidden;}}
.label{{font-size:14px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;padding:12px 18px;background:rgba(0,0,0,0.6);position:absolute;top:0;left:0;z-index:10;border-radius:0 0 12px 0;}}
.bg{{position:absolute;inset:0;}}
.bg img{{width:100%;height:100%;object-fit:cover;}}
.dim{{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,transparent 0%,rgba(0,0,0,0.5) 50%,rgba(0,0,0,0.9) 100%);}}
.z1{{position:relative;z-index:3;}}
.shadow{{text-shadow:0 3px 30px rgba(0,0,0,0.8);}}
.s3{{justify-content:flex-end;}}
.s3 .content{{padding:60px 80px;}}
.s3 .tag{{font-size:14px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;margin-bottom:24px;}}
.s3 .title{{font-family:'Space Grotesk',sans-serif;font-size:72px;font-weight:700;line-height:1.15;color:#F0E8DC;margin-bottom:24px;}}
.s3 .title em{{font-style:italic;color:#7ecfa8;}}
.s3 .body{{font-size:26px;font-weight:300;line-height:1.7;color:rgba(240,232,220,0.65);max-width:700px;}}
</style></head><body>
<div class="slide s3">
  <div class="bg"><img src="{img}" onerror="this.style.display='none'"></div>
  <div class="dim"></div>
  <div class="label">{num} — Hero</div>
  <div class="content z1">
    <div class="tag">{tag}</div>
    <div class="title shadow">{title}</div>
    <div class="body shadow">{body}</div>
  </div>
</div></body></html>"""


def _render_quote(data, num, total, bg_url):
    quote = data.get("quote", "Cita")
    author = data.get("author", "")
    img = data.get("image_url", bg_url or "")

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;900&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#000;color:#F0E8DC;font-family:'Plus Jakarta Sans',sans-serif;}}
.slide{{width:1080px;height:1350px;display:flex;flex-direction:column;position:relative;overflow:hidden;}}
.label{{font-size:14px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;padding:12px 18px;background:rgba(0,0,0,0.6);position:absolute;top:0;left:0;z-index:10;border-radius:0 0 12px 0;}}
.bg{{position:absolute;inset:0;}}
.bg img{{width:100%;height:100%;object-fit:cover;}}
.dim{{position:absolute;inset:0;z-index:2;background:radial-gradient(ellipse at center,rgba(0,0,0,0.4) 0%,rgba(0,0,0,0.75) 100%);}}
.z1{{position:relative;z-index:3;}}
.shadow{{text-shadow:0 3px 30px rgba(0,0,0,0.8);}}
.s4{{align-items:center;justify-content:center;text-align:center;padding:80px;}}
.s4 .qmark{{font-size:130px;line-height:0.5;font-weight:900;color:rgba(126,207,168,0.20);margin-left:-6px;margin-bottom:28px;}}
.s4 .quote{{font-family:'Plus Jakarta Sans';font-size:46px;font-weight:300;line-height:1.06;color:rgba(240,232,220,0.55);letter-spacing:-0.01em;margin-bottom:6px;}}
.s4 .author{{font-size:24px;font-weight:300;line-height:1.50;color:rgba(240,232,220,0.40);font-style:italic;margin-top:20px;}}
.s4 .line{{width:100%;height:1px;background:linear-gradient(to right,rgba(126,207,168,0.40),transparent);margin:28px 0;}}
</style></head><body>
<div class="slide s4">
  <div class="bg"><img src="{img}" onerror="this.style.display='none'"></div>
  <div class="dim"></div>
  <div class="label">{num} — Quote</div>
  <div class="qmark z1">&ldquo;</div>
  <div class="quote shadow z1">{quote}</div>
  <div class="line z1"></div>
  <div class="author shadow z1">{author}</div>
</div></body></html>"""


def _render_cta(data, num, total, bg_url):
    title = data.get("title", "Título")
    body = data.get("body", "")
    cta_text = data.get("cta_text", "Comenzar →")
    cta_url = data.get("cta_url", "endonautas.cl")
    img = data.get("image_url", bg_url or "")

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;900&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#000;color:#F0E8DC;font-family:'Plus Jakarta Sans',sans-serif;}}
.slide{{width:1080px;height:1350px;display:flex;flex-direction:column;position:relative;overflow:hidden;}}
.label{{font-size:14px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;padding:12px 18px;background:rgba(0,0,0,0.6);position:absolute;top:0;left:0;z-index:10;border-radius:0 0 12px 0;}}
.bg{{position:absolute;inset:0;}}
.bg img{{width:100%;height:100%;object-fit:cover;}}
.dim{{position:absolute;inset:0;z-index:2;background:radial-gradient(ellipse at center,transparent 20%,rgba(0,0,0,0.6) 100%),linear-gradient(180deg,rgba(0,0,0,0.3) 0%,rgba(0,0,0,0.85) 100%);}}
.z1{{position:relative;z-index:3;}}
.shadow{{text-shadow:0 3px 30px rgba(0,0,0,0.8);}}
.s5{{align-items:center;justify-content:center;text-align:center;padding:80px;}}
.s5 .logo{{display:flex;align-items:center;justify-content:center;gap:14px;margin-bottom:40px;}}
.s5 .logo span{{font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:600;letter-spacing:5px;text-transform:uppercase;color:#7ecfa8;}}
.s5 .title{{font-family:'Space Grotesk',sans-serif;font-size:80px;font-weight:700;line-height:1.1;color:#F0E8DC;margin-bottom:30px;}}
.s5 .title em{{font-style:italic;color:#7ecfa8;}}
.s5 .line{{width:60px;height:2px;background:rgba(126,207,168,0.5);margin:0 auto 30px;}}
.s5 .body{{font-size:28px;font-weight:300;line-height:1.7;color:rgba(240,232,220,0.75);max-width:720px;}}
.s5 .url{{font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:600;color:#7ecfa8;margin-top:40px;padding:14px 36px;border:1px solid rgba(126,207,168,0.25);border-radius:100px;display:inline-block;}}
</style></head><body>
<div class="slide s5">
  <div class="bg"><img src="{img}" onerror="this.style.display='none'"></div>
  <div class="dim"></div>
  <div class="label">{num} — CTA</div>
  <div class="logo z1"><span>Endonautas</span></div>
  <div class="title shadow z1">{title}</div>
  <div class="line z1"></div>
  <div class="body shadow z1">{body}</div>
  <div class="url shadow z1">{cta_text}</div>
</div></body></html>"""


def _render_lista(data, num, total, bg_url):
    tag = data.get("tag", "CLAVES")
    title = data.get("title", "Título")
    points = data.get("points", [])
    img = data.get("image_url", bg_url or "")

    points_html = "".join([f'<li style="font-size:26px;font-weight:300;line-height:1.6;color:rgba(240,232,220,0.70);margin-bottom:16px;">{p}</li>' for p in points])

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;900&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#0a0a0f;color:#F0E8DC;font-family:'Plus Jakarta Sans',sans-serif;}}
.slide{{width:1080px;height:1350px;display:flex;flex-direction:column;position:relative;overflow:hidden;}}
.label{{font-size:14px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;padding:12px 18px;background:rgba(0,0,0,0.6);position:absolute;top:0;left:0;z-index:10;border-radius:0 0 12px 0;}}
.bg{{position:absolute;inset:0;}}
.bg img{{width:100%;height:100%;object-fit:cover;opacity:0.2;}}
.dim{{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(10,10,15,0.7) 0%,rgba(10,10,15,0.9) 100%);}}
.z1{{position:relative;z-index:3;}}
.shadow{{text-shadow:0 3px 30px rgba(0,0,0,0.8);}}
.s6{{padding:80px;}}
.s6 .tag{{font-size:14px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;margin-bottom:28px;}}
.s6 .title{{font-family:'Space Grotesk',sans-serif;font-size:64px;font-weight:700;line-height:1.15;margin-bottom:40px;}}
.s6 .title em{{font-style:italic;color:#7ecfa8;}}
.s6 .points{{list-style:none;padding:0;}}
.s6 .points li{{padding-left:32px;position:relative;}}
.s6 .points li::before{{content:"→";position:absolute;left:0;color:#7ecfa8;font-weight:600;}}
</style></head><body>
<div class="slide s6">
  <div class="bg"><img src="{img}" onerror="this.style.display='none'"></div>
  <div class="dim"></div>
  <div class="label">{num} — Lista</div>
  <div class="z1">
    <div class="tag shadow">{tag}</div>
    <div class="title shadow">{title}</div>
    <ul class="points shadow">{points_html}</ul>
  </div>
</div></body></html>"""


def _render_dato(data, num, total, bg_url):
    dato = data.get("dato", "Dato impactante")
    contexto = data.get("contexto", "")
    img = data.get("image_url", bg_url or "")

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;900&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#000;color:#F0E8DC;font-family:'Plus Jakarta Sans',sans-serif;}}
.slide{{width:1080px;height:1350px;display:flex;flex-direction:column;position:relative;overflow:hidden;}}
.label{{font-size:14px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;padding:12px 18px;background:rgba(0,0,0,0.6);position:absolute;top:0;left:0;z-index:10;border-radius:0 0 12px 0;}}
.bg{{position:absolute;inset:0;}}
.bg img{{width:100%;height:100%;object-fit:cover;}}
.dim{{position:absolute;inset:0;z-index:2;background:radial-gradient(ellipse at center,transparent 20%,rgba(0,0,0,0.7) 100%);}}
.z1{{position:relative;z-index:3;}}
.glow{{text-shadow:0 0 60px rgba(126,207,168,0.3),0 3px 30px rgba(0,0,0,0.8);}}
.s7{{align-items:center;justify-content:center;text-align:center;padding:80px;}}
.s7 .dato{{font-family:'Space Grotesk',sans-serif;font-size:120px;font-weight:900;line-height:1.05;color:#F0E8DC;margin-bottom:30px;}}
.s7 .dato em{{font-style:italic;color:#7ecfa8;}}
.s7 .line{{width:60px;height:2px;background:rgba(126,207,168,0.5);margin:0 auto 30px;}}
.s7 .contexto{{font-size:28px;font-weight:300;line-height:1.7;color:rgba(240,232,220,0.65);max-width:720px;}}
</style></head><body>
<div class="slide s7">
  <div class="bg"><img src="{img}" onerror="this.style.display='none'"></div>
  <div class="dim"></div>
  <div class="label">{num} — Dato</div>
  <div class="dato glow z1">{dato}</div>
  <div class="line z1"></div>
  <div class="contexto shadow z1">{contexto}</div>
</div></body></html>"""


def _render_blur(data, num, total, bg_url):
    tag = data.get("tag", "CLAVE")
    title = data.get("title", "Título")
    body = data.get("body", "Contenido")
    img = data.get("image_url", bg_url or "")

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;900&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#000;color:#F0E8DC;font-family:'Plus Jakarta Sans',sans-serif;}}
.slide{{width:1080px;height:1350px;display:flex;flex-direction:column;position:relative;overflow:hidden;}}
.label{{font-size:14px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#7ecfa8;padding:12px 18px;background:rgba(0,0,0,0.6);position:absolute;top:0;left:0;z-index:10;border-radius:0 0 12px 0;}}
.bg{{position:absolute;inset:0;}}
.bg img{{width:100%;height:100%;object-fit:cover;}}
.dim{{position:absolute;inset:0;z-index:2;background:rgba(0,0,0,0.5);}}
.z1{{position:relative;z-index:3;}}
.shadow{{text-shadow:0 3px 30px rgba(0,0,0,0.8);}}
.s8{{align-items:center;justify-content:center;padding:80px;}}
.s8 .card{{background:rgba(126,207,168,0.06);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border:1px solid rgba(126,207,168,0.14);border-left:2.5px solid #7ecfa8;border-radius:0 4px 4px 0;padding:40px;max-width:800px;}}
.s8 .tag{{font-family:'Plus Jakarta Sans';font-size:12px;letter-spacing:3px;text-transform:uppercase;color:#7ecfa8;margin-bottom:16px;}}
.s8 .title{{font-family:'Space Grotesk',sans-serif;font-size:56px;font-weight:700;line-height:1.15;margin-bottom:20px;}}
.s8 .title em{{font-style:italic;color:#7ecfa8;}}
.s8 .body{{font-size:24px;font-weight:300;line-height:1.6;color:rgba(240,232,220,0.72);}}
</style></head><body>
<div class="slide s8">
  <div class="bg"><img src="{img}" onerror="this.style.display='none'"></div>
  <div class="dim"></div>
  <div class="label">{num} — Blur Card</div>
  <div class="card z1">
    <div class="tag">{tag}</div>
    <div class="title shadow">{title}</div>
    <div class="body shadow">{body}</div>
  </div>
</div></body></html>"""
