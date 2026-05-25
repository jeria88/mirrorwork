# MirrorWork — Registro de progreso

## 2026-05-25 — Blog submission modal + postulaciones

### ✅ Completado
- Modal "Postular al blog" en `base.html` (bottom-sheet, mismo patrón que share-modal)
  - Fetch prefill desde `/blog/postular/prefill/<type>/<id>/`
  - Editable antes de enviar — estados: loading → form → success
  - Botones: "Guardar borrador" / "Enviar para revisión →"
- Botón "Postular al blog" en `mirror/espejo.html` (header del chat, cuando hay mensajes)
- Botón "Postular al blog" en `psychometrics/test_result.html` (action-row, acento gold)
- Botón "✦ Postular al blog" en `birth/lectura.html` (estado revealed)

### 🔶 Pendiente
- Nav cross-site: barra superior con links a endonautas.cl cuando el usuario no está autenticado
- Conectar fractones en Espejo: `spend(user, 'espejo_exchange')` en `espejo_send`
- Conectar fractones en AI insights: `spend(user, 'ai_insight')` antes de DeepSeek
- `credit_mission(user, 'onboarding')` al final de `onboarding_viaje`
- Fondos árbol y archipiélago (mandala ✅)
- Hotmart packs: crear productos, agregar offer codes a Railway env vars

---

## 2026-05-12 — Espejo, KB, lecturas de nacimiento, comunidad, fondos

### ✅ Completado

#### Base de conocimientos (KB) del Espejo
- `MirrorDocumento` + `MirrorChunk` con soporte de embeddings
- `seed_mirror_kb` — 40 documentos, 97 chunks (ebook, marco_teorico, tradicion)
- RAG con cosine similarity en Python puro + fallback keyword overlap

#### Espejo de Conflictos
- Pipeline AJAX completo: RAG → DeepSeek → guardar → JSON
- Historial[-12:] + contexto KB + resumen de tests del usuario
- Memorias del Espejo (`EspejoMemoria`) — versionadas, activables
- `pregunta_retorno`: muestra la pregunta de cierre de hace un mes para explorarla hoy
- Template `espejo.html` — 3 columnas: sidebar sesiones, chat, panel lecturas
- Burbuja flotante `◎` en base.html

#### Psychometrics
- `_generate_ai_insight()` — lectura endonauta 3-4 párrafos vía DeepSeek
- `insight_view` — vista dedicada para la lectura
- `my_results` — historial completo de resultados del usuario

#### Birth (lecturas de nacimiento)
- `BirthProfile` + `BirthReport` (astral, human_design, saju)
- Lecturas endonautas generadas por IA asíncronamente
- Template `lectura.html` con estados: pending → loading (polling) → revealed
- `SECTIONS_CONFIG` por tipo de lectura con colores e iconos

#### Community
- Feed con `SharedInsight` — compartir resultados de tests y sesiones del Espejo
- Reposts, reacciones (resonó / lo_vivo / gracias), comentarios
- Follows, mensajes directos
- Perfiles públicos/privados

#### Fondos visuales
- Cosmos: agujero negro kepleriano Three.js con presets por sección
- Mandala: Canvas 2D paramétrico con simetría variable
- Psicodélico: Canvas 2D con transiciones de escenas
- `map_aesthetic` en `UserProfile` controla el fondo activo

#### Tokens / Fractones
- `TokenBalance.spend()` — descuenta monthly primero, luego permanent
- Misiones (idempotentes): onboarding (+60), first_test (+20), first_espejo (+40), first_dimension (+50)
- Webhook Hotmart: activar/revocar planes, packs de fractones
- Vistas `balance` + `planes`

#### Practitioners
- Perfiles temporales con UUID de acceso compartible
- Asignación de tests, vista de resultados del cliente

#### Reports
- Dashboard de progreso: stats totales + breakdown por dimensión

#### Nav y base.html
- SPA navigation con iris clip-path effect
- Mixer FAB con controles del fondo
- Dock inferior con navegación principal
- Share modal para compartir insights
- Balance de fractones en tiempo real en el nav
