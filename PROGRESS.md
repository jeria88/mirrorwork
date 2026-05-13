# MirrorWork — Registro de progreso

## Sesión actual (2026-05-12)

### ✅ Completado

#### Base de conocimientos (KB) del Espejo
- Modelos `MirrorDocumento` + `MirrorChunk` con soporte de embeddings (JSONField)
- `seed_mirror_kb` — 40 documentos, 97 chunks en 3 categorías (ebook, marco_teorico, tradicion)
- `index_mirror_docs` — generación de embeddings OpenAI con fallback keyword
- RAG con cosine similarity en Python puro (sin numpy, compatible con RAM < 4GB)
- Fallback por keyword overlap cuando no hay embeddings

#### Espejo de Conflictos (mirror app)
- `espejo_home` — sidebar de sesiones + chat area
- `espejo_nuevo` — crea sesión y redirige
- `espejo_send` — pipeline AJAX completo: RAG → DeepSeek → guardar → JSON
- `espejo_archivar` — archiva sesión
- Template `espejo.html` — UI de chat con typing indicator, welcome chips, auto-resize textarea
- Burbuja flotante `◎` en `base.html` para acceso rápido al Espejo
- Test end-to-end confirmado: RAG recupera chunks relevantes, DeepSeek responde en tono endonauta

#### AI Insights en tests (psychometrics)
- `_generate_ai_insight()` — llama a DeepSeek con resultados del test, genera lectura endonauta 3-4 párrafos
- `test_submit` — intenta generar insight y descontar 5 tokens al guardar resultado
- `test_result.html` — sección "Lectura del Espejo ◎" aparece cuando hay `ai_insight`

#### Sistema de tokens (tokens app)
- `TokenBalance.spend()` y `credit()` con `TokenTransaction` ya existían
- Vista `balance` — saldo actual + últimos 30 movimientos + info de plan
- Vista `planes` — página de precios con los 3 planes, CTAs a Hotmart, FAQ
- `templates/tokens/balance.html` — muestra plan actual con link a upgrade
- `templates/tokens/planes.html` — pricing page completa

#### Integración Hotmart
- `tokens/hotmart.py` — lógica core de procesamiento de webhooks
  - `ACTIVATE_EVENTS`: `PURCHASE_APPROVED`, `PURCHASE_COMPLETE`
  - `REVOKE_EVENTS`: `PURCHASE_REFUNDED`, `PURCHASE_CHARGEBACK`, `PURCHASE_CANCELED`, `SUBSCRIPTION_CANCELLATION`
  - `activate_plan()` — actualiza `UserProfile.plan`, guarda `hotmart_subscriber_code`, acredita tokens mensuales
  - `revoke_plan()` — baja a Free, limpia subscriber code
- `hotmart_webhook` view — verifica `hottok` / `X-Hotmart-Webhook-Token`, parsea evento, llama a `process_webhook()`
- `UserProfile.hotmart_subscriber_code` — campo nuevo + migración aplicada
- `settings.py` — `HOTMART_WEBHOOK_TOKEN`, `HOTMART_PRODUCT_PLAN_MAP`, `HOTMART_CHECKOUT_URLS` desde env vars

#### Practitioners app
- `perfil_lista` — grid de perfiles activos con barra de tokens
- `perfil_crear` — POST con alias, notas, token_allocation
- `perfil_detalle` — resultados del cliente + enlace UUID de acceso compartible
- `perfil_archivar` — soft delete (active=False)
- Templates: `lista.html` (con modal inline de creación) + `detalle.html`

#### Reports app
- `dashboard` — stats: tests totales, dimensiones exploradas, sesiones Espejo
- Template `dashboard.html` — cards de stats + breakdown por dimensión + recientes

#### Nav y base.html
- Links añadidos: Espejo, Progreso, Clientes, Planes
- Balance de tokens en tiempo real en el nav (acento verde)
- Burbuja flotante `◎` Espejo de Conflictos

#### Infraestructura Railway
- `Procfile` — secuencia completa: migrate → seed_tests → seed_mirror_kb → collectstatic → gunicorn
- `railway.toml` — startCommand, política de reintentos
- `settings.py` — `RAILWAY_PUBLIC_DOMAIN` auto-detectado, `CSRF_TRUSTED_ORIGINS`, HTTPS security flags cuando `DEBUG=False`

---

## 🔶 Pendiente (en orden de prioridad)

### Crítico antes de lanzar

| # | Tarea | Detalle |
|---|-------|---------|
| 1 | **Configurar Hotmart** | Crear los 2 productos en Hotmart, copiar IDs y URLs al `.env` de Railway |
| 2 | **`git init` + push a GitHub** | Primer commit, repositorio privado |
| 3 | **Deploy a Railway** | Conectar GitHub repo, añadir PostgreSQL plugin, configurar todas las env vars |
| 4 | **Enforcement de plan en Practitioners** | Verificar `request.user.profile.is_practicante` antes de permitir crear/ver perfiles de clientes |
| 5 | **Admin Django configurado** | Registrar todos los modelos en `admin.py` para gestión manual de usuarios/planes |

### Features importantes

| # | Tarea | Detalle |
|---|-------|---------|
| 6 | **Renovación mensual de tokens** | Cronjob o Railway Cron que acredita tokens mensuales a suscriptores activos el día 1 de cada mes |
| 7 | **Enlace de acceso para clientes** (`/practicantes/acceso/<uuid>/`) | La URL existe en el template pero la view no está implementada — el cliente debe poder tomar tests desde ese enlace sin registrarse |
| 8 | **Portal de gestión para clientes en Hotmart** | Añadir link "Gestionar suscripción" que apunte al portal de Hotmart (URL fija) |
| 9 | **Tokens acumulativos opcionales** | Decidir si los tokens no usados se pierden o acumulan (actualmente se pierden) |
| 10 | **Notificación por email** | Email de bienvenida al activar plan + aviso cuando tokens < 20 |

### Instrumentos a auditar (psicometría)

| Test | Problema | Solución |
|------|----------|---------|
| ECR | ~10 ítems actual | ECR-R (36 ítems) o ECR-12, escala likert7 |
| SOC-29 | 7 ítems actual | SOC-29 (29 ítems bipolar) o SOC-13 (13 ítems validados) |
| MAIA | 21 ítems likert5 | MAIA-2 tiene 37 ítems escala 0-5 |
| DERS-16 | 8 ítems custom | DERS-16 versión validada con 16 ítems likert5 |
| PSQI | Suma simple | 7 componentes con ponderación diferente por ítem |

### UI / Mejoras visuales

| # | Tarea |
|---|-------|
| 11 | Mejorar contraste en opciones de `test_take.html` (difíciles de distinguir en escala) |
| 12 | Decidir paleta definitiva y eliminar theme switcher temporal de `base.html` |
| 13 | Personalización de paleta de color por usuario (preferencia en perfil) |
| 14 | Página de perfil de usuario editable (bio, profesión, foto) |

### DevOps / Seguridad

| # | Tarea |
|---|-------|
| 15 | Generar `SECRET_KEY` segura para producción (`secrets.token_urlsafe(50)`) |
| 16 | Configurar `ALLOWED_HOSTS` con dominio real de Railway |
| 17 | Añadir `runtime.txt` con `python-3.12.0` (ya existe) |
| 18 | Revisar que `staticfiles/` esté en `.gitignore` |

---

## Migraciones aplicadas

| App | Migración |
|-----|-----------|
| accounts | `0001_initial`, `0002_add_hotmart_subscriber_code` |
| psychometrics | `0001_initial`, `0002_add_likert3_scale`, `0003_add_likert5a_scale`, `0004_add_instrument_type` |
| mirror | `0001_initial`, `0002_mirror_kb` |
| practitioners | `0001_initial` |
| tokens | `0001_initial` |

---

## Estado de datos (local)

```
Tests psicométricos : 35
KB Mirror chunks    : 97 (sobre 40 documentos)
KB embeddings       : pendiente (requiere OPENAI_API_KEY)
```
