# MirrorWork — Registro de progreso

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
