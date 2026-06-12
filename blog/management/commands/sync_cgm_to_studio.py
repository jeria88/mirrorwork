import json
import os
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from blog.models import GeneratedArticle, SocialPost

class Command(BaseCommand):
    help = 'Sincroniza y carga reels y carruseles generados anteriormente en la base de datos de Django a los archivos JSON del Content Studio'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando sincronización de contenidos desde la base de datos al Content Studio...")

        # Rutas de archivos JSON del Content Studio
        base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        studio_data_dir = base_dir / 'studio' / 'data'
        studio_data_dir.mkdir(parents=True, exist_ok=True)

        carruseles_json_path = studio_data_dir / 'carruseles_data.json'
        reels_json_path = studio_data_dir / 'reels_data.json'
        remotion_reels_path = base_dir / 'contenido' / 'reels' / 'remotion' / 'src' / 'reels_data.json'

        # Cargar datos existentes o inicializar
        carruseles_data = []
        if carruseles_json_path.exists():
            try:
                with open(carruseles_json_path, 'r', encoding='utf-8') as f:
                    carruseles_data = json.load(f)
            except Exception as e:
                self.stderr.write(f"Error cargando carruseles_data.json: {e}")

        reels_data = []
        if reels_json_path.exists():
            try:
                with open(reels_json_path, 'r', encoding='utf-8') as f:
                    reels_data = json.load(f)
            except Exception as e:
                self.stderr.write(f"Error cargando reels_data.json: {e}")

        existing_carrusel_ids = {c['id'] for c in carruseles_data}
        existing_reel_ids = {r['id'] for r in reels_data}

        imported_carruseles_count = 0
        imported_reels_count = 0

        # --- 1. Importar desde GeneratedArticle (carruseles con slides_data) ---
        articles = GeneratedArticle.objects.all()
        for art in articles:
            # Si tiene slides_data y contiene slides estructurados
            slides_data_field = art.slides_data or {}
            slides_list = []
            if isinstance(slides_data_field, dict):
                slides_list = slides_data_field.get('slides', [])
            elif isinstance(slides_data_field, list):
                slides_list = slides_data_field

            if slides_list:
                c_id = f"GA_{art.pk}"
                if c_id not in existing_carrusel_ids:
                    # Formatear slides
                    slides_formatted = []
                    for i, sl in enumerate(slides_list):
                        text = sl.get('title') or sl.get('text') or sl.get('body') or ""
                        body = sl.get('body', "") if sl.get('title') else ""
                        
                        slide_type = "hook" if i == 0 else "content"
                        slide_obj = {
                            "type": slide_type,
                            "headline": text,
                            "body": body,
                            "eyebrow": sl.get('tag', '')
                        }
                        if i == 0 or i == len(slides_list) - 1:
                            slide_obj["ctaText"] = sl.get('cta', "→ Desliza para continuar" if i == 0 else "@endonautas")
                        
                        slides_formatted.append(slide_obj)

                    new_carrusel = {
                        "id": c_id,
                        "title": art.title,
                        "file": slugify(art.title),
                        "phase": "Migrado",
                        "caption": art.intro or art.meta_description or f"Artículo: {art.title}\n\nDescubre más en endonautas.cl",
                        "slides": slides_formatted
                    }
                    carruseles_data.append(new_carrusel)
                    existing_carrusel_ids.add(c_id)
                    imported_carruseles_count += 1
                    self.stdout.write(f"  + Carrusel importado desde artículo: {art.title} (ID: {art.pk})")

        # --- 2. Importar desde SocialPost ---
        social_posts = SocialPost.objects.all()
        for post in social_posts:
            title = post.generated_article.title if post.generated_article else (post.blog_post.title if post.blog_post else f"Post RRSS {post.pk}")
            
            # --- Carruseles ---
            if post.formato == SocialPost.FORMATO_CARRUSEL:
                c_id = f"SP_{post.pk}"
                if c_id not in existing_carrusel_ids:
                    # Parsear slides desde carrusel_cuerpo
                    slides_text = []
                    if post.carrusel_cuerpo:
                        # Dividir por "---" o saltos de línea con guiones si es que se separaron así
                        parts = re.split(r'\s*---\s*', post.carrusel_cuerpo)
                        slides_text = [p.strip() for p in parts if p.strip()]
                    
                    if not slides_text and post.carrusel_gancho:
                        slides_text = [post.carrusel_gancho]
                    
                    slides_formatted = []
                    # Añadir Hook
                    hook_text = post.carrusel_gancho or (slides_text[0] if slides_text else title)
                    slides_formatted.append({
                        "type": "hook",
                        "headline": hook_text,
                        "body": "",
                        "eyebrow": "Espejo",
                        "ctaText": post.carrusel_cta or "→ Desliza para entender"
                    })
                    
                    # Añadir Content slides
                    for i, t in enumerate(slides_text):
                        if i == 0 and t == hook_text:
                            continue # Evitar duplicado de hook si estaba en el cuerpo
                        slides_formatted.append({
                            "type": "content",
                            "headline": t,
                            "body": ""
                        })
                        
                    # Asegurar slide final de CTA si hay CTA
                    if post.carrusel_cta and len(slides_formatted) > 1:
                        slides_formatted[-1]["ctaText"] = post.carrusel_cta
                        slides_formatted[-1]["eyebrow"] = "Llamado a la acción"

                    new_carrusel = {
                        "id": c_id,
                        "title": title,
                        "file": slugify(title),
                        "phase": "Migrado",
                        "caption": post.carrusel_descripcion or f"{hook_text}\n\n" + "\n\n".join(slides_text) + f"\n\n{post.carrusel_cta}\n\n{post.carrusel_hashtags}",
                        "slides": slides_formatted
                    }
                    carruseles_data.append(new_carrusel)
                    existing_carrusel_ids.add(c_id)
                    imported_carruseles_count += 1
                    self.stdout.write(f"  + Carrusel importado desde post de red social: {title} (ID: {post.pk})")

            # --- Reels ---
            elif post.formato == SocialPost.FORMATO_REEL:
                r_id = f"SP_{post.pk}"
                if r_id not in existing_reel_ids:
                    gancho = post.reel_gancho or title
                    cuerpo = post.reel_cuerpo or ""
                    cta = post.reel_cta or "Descubre más en endonautas.cl"

                    # Dividir cuerpo en oraciones para hacer escenas fluidas
                    paragraphs = [p.strip() for p in re.split(r'\n+|\.\s+', cuerpo) if p.strip()]
                    if not paragraphs:
                        paragraphs = ["Continúa tu viaje interior."]

                    scenes = []
                    current_time = 0

                    # 1. Escena Gancho (Portada del Reel)
                    scenes.append({
                        "from": current_time,
                        "duration": 4,
                        "padding": "100px 0",
                        "elements": [
                            { "type": "logo", "delay": 10 },
                            { "type": "text", "text": gancho, "delay": 15, "font": "playfair", "size": 60, "weight": 700, "color": "gold" }
                        ]
                    })
                    current_time += 4

                    # 2. Escenas de Cuerpo
                    for para in paragraphs:
                        scenes.append({
                            "from": current_time,
                            "duration": 5,
                            "padding": "80px 0",
                            "elements": [
                                { "type": "text", "text": para, "delay": 10, "font": "inter", "size": 32 }
                            ]
                        })
                        current_time += 5

                    # 3. Escena final de CTA
                    scenes.append({
                        "from": current_time,
                        "duration": 5,
                        "padding": "100px 0",
                        "elements": [
                            { "type": "text", "text": cta, "delay": 15, "font": "inter", "size": 30, "color": "gold", "border": True },
                            { "type": "logo", "delay": 90 }
                        ]
                    })
                    current_time += 5

                    new_reel = {
                        "id": r_id,
                        "title": title,
                        "duration": current_time,
                        "scenes": scenes
                    }
                    reels_data.append(new_reel)
                    existing_reel_ids.add(r_id)
                    imported_reels_count += 1
                    self.stdout.write(f"  + Reel importado desde post de red social: {title} (ID: {post.pk})")

        # Guardar archivos JSON actualizados
        if imported_carruseles_count > 0 or not carruseles_json_path.exists():
            try:
                with open(carruseles_json_path, 'w', encoding='utf-8') as f:
                    json.dump(carruseles_data, f, indent=2, ensure_ascii=False)
                self.stdout.write(self.style.SUCCESS(f"Sincronizados {imported_carruseles_count} carruseles en {carruseles_json_path}"))
            except Exception as e:
                self.stderr.write(f"Error escribiendo carruseles_data.json: {e}")

        if imported_reels_count > 0 or not reels_json_path.exists():
            try:
                with open(reels_json_path, 'w', encoding='utf-8') as f:
                    json.dump(reels_data, f, indent=2, ensure_ascii=False)
                self.stdout.write(self.style.SUCCESS(f"Sincronizados {imported_reels_count} reels en {reels_json_path}"))
                
                # También sincronizar a remotion
                remotion_reels_path.parent.mkdir(parents=True, exist_ok=True)
                with open(remotion_reels_path, 'w', encoding='utf-8') as f:
                    json.dump(reels_data, f, indent=2, ensure_ascii=False)
                self.stdout.write(self.style.SUCCESS(f"Sincronizado reels_data.json en Remotion ({remotion_reels_path})"))
            except Exception as e:
                self.stderr.write(f"Error escribiendo reels_data.json: {e}")

        self.stdout.write(self.style.SUCCESS(f"Proceso finalizado. Total importado: {imported_carruseles_count} carruseles, {imported_reels_count} reels."))
