# MirrorWork — Registro de progreso

## 2026-06-12 — Integración Content Studio (CGM), Sincronización e Inicio en Railway

### ✅ Completado

#### Content Studio & Previsualización de Activos
- **Filtro de cabeceras en Proxy**: Corregido el error `500 AssertionError` al previsualizar videos (.mp4) y carruseles (.png) mediante el proxy de Django. Se filtraron cabeceras *hop-by-hop* (`Connection`, `Keep-Alive`, `Proxy-Authenticate`, `Proxy-Authorization`, `TE`, `Trailers`, `Transfer-Encoding`, `Upgrade`) y `Content-Encoding` en [views_studio.py](file:///home/nikka/Proyectos/endonautas/mirrorwork/centro/views_studio.py).
- **Ruta de Login de Centro**: Corregidas las redirecciones de inicio de sesión de `/django-admin/login/` a `/admin/login/` en [views.py](file:///home/nikka/Proyectos/endonautas/mirrorwork/centro/views.py).
- **Control estricto de HTTP**: Modificado el proxy para filtrar cabeceras con valores vacíos (e.g. `Content-Length: ''` en peticiones GET) que causaban errores `400 Bad Request` en el servidor Express.

#### Sincronización de Base de Datos
- **Sincronización a JSON**: Creado el comando de gestión Django `sync_cgm_to_studio` en [sync_cgm_to_studio.py](file:///home/nikka/Proyectos/endonautas/mirrorwork/blog/management/commands/sync_cgm_to_studio.py). Este script importa automáticamente los artículos (`GeneratedArticle` slides_data) y posts (`SocialPost`) almacenados en PostgreSQL y los integra en `studio/data/reels_data.json` y `studio/data/carruseles_data.json`.
- **Automatización en el arranque**: Agregado el paso `python manage.py sync_cgm_to_studio` en el archivo de inicio [start.sh](file:///home/nikka/Proyectos/endonautas/mirrorwork/scripts/start.sh) para reconstruir los archivos JSON dinámicamente en Railway con cada arranque del contenedor.
- **Estrategia de Persistencia**: Documentado el esquema de montaje de volúmenes persistentes en Railway para resguardar la base de datos de JSONs y los archivos multimedia generados (`/app/studio/data`, `/app/contenido/carruseles/pngs`, `/app/contenido/reels/mp4`, `/app/contenido/reels/scripts`).

#### Soporte Cloudflare R2
- **Integración de S3**: Añadidas las librerías `django-storages[s3]` y `boto3` a [requirements.txt](file:///home/nikka/Proyectos/endonautas/mirrorwork/requirements.txt) y cargadas en el entorno local.
- **Configuración Dinámica**: Modificado [settings.py](file:///home/nikka/Proyectos/endonautas/mirrorwork/config/settings.py) para utilizar el backend `S3Storage` apuntando a Cloudflare R2 únicamente si las variables de entorno AWS están presentes. Si no lo están, el sistema realiza un fallback automático al sistema de archivos local (`FileSystemStorage`).
- **Variables de Entorno**: Registradas las credenciales y el dominio del bucket público `pub-d9b36e28a45945e0bc585b34b4647451.r2.dev` en el archivo [.env](file:///home/nikka/Proyectos/endonautas/mirrorwork/.env).

### 🔶 Pendiente
- Configurar las variables de entorno de Cloudflare R2 en el panel de control de Railway.
- Monitorear el despliegue automático de Railway tras el push a `main`.


---

## 2026-06-03 — Fix migraciones + Community posts nativos

### ✅ Completado

#### Fix migraciones
- Eliminadas migraciones `0011_userprofile_active_template` y `0012_alter_userprofile_map_aesthetic_and_more`
- Estas migraciones dependían de `background.0001_initial` (app inexistente)
- Actualizada `0013_remove_active_template_add_estrellas` para depender de `0010` directamente
- Fix: `NodeNotFoundError` en Railway deploy resuelto

#### Community — Posts nativos
- `SharedInsight`: nuevo `source_type = 'native'` para posts de foto + texto libre
- Campos `text` (TextField) e `image` (ImageField) en SharedInsight
- Vista `compartir` actualizada: acepta FormData (con imagen) y JSON
- Feed actualizado: muestra imagen del post, texto unificado, badge "Publicación"
- Botón "Nueva publicación" con modal en feed.html
- Preview de imagen antes de publicar
- JavaScript para envío con FormData
- Migración `0003_sharedinsight_native.py`

### 🔶 Pendiente
- Verificar que `generate_v4.py` existe en Railway (para carruseles platform)
- Conectar fractones en Espejo: `spend(user, 'espejo_exchange')` + `credit_mission(user, 'first_espejo')`
- Conectar fractones en AI insights: `spend(user, 'ai_insight')` antes de DeepSeek
- `credit_mission(user, 'onboarding')` al final de `onboarding_viaje`
- Hotmart packs: crear 3 productos, vars `HOTMART_PACK_200/600/2000` en Railway

---

## 2026-05-29 — Auditoría cross-site, copy ecosistema
[Ver PROGRESS.md completo para detalles anteriores]

---

## 2026-05-25 — Blog submission modal + postulaciones
[Ver PROGRESS.md completo para detalles anteriores]

---

## 2026-05-12 — Espejo, KB, lecturas de nacimiento, comunidad, fondos
[Ver PROGRESS.md completo para detalles anteriores]
