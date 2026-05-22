# MirrorWork — Instrucciones para Claude

## Comando siempre: `python3 manage.py` (nunca `python`)

## Stack
- Django 6, SQLite (dev), Railway (deploy target)
- WhiteNoise para static files
- DeepSeek API (key en `.env`) para AI insights
- Git activo, repo en GitHub, deploy en Railway

## Arrancar el servidor
```bash
python3 manage.py runserver 8001
python3 manage.py seed_tests --force    # recarga los 35 tests
python3 manage.py seed_missions         # crea/actualiza las 4 misiones
python3 manage.py migrate
```

## Estructura de apps
| App | Estado | Descripción |
|-----|--------|-------------|
| `accounts` | ✅ activa | User (AbstractUser, email como USERNAME_FIELD), login/register/dashboard, mapa interior |
| `psychometrics` | ✅ activa | Tests, preguntas, resultados, evaluador, seed |
| `mirror` | 🔶 en progreso | KB lista (40 docs, 97 chunks, 43 autores). Falta: views AJAX, template conversación, burbuja flotante |
| `tokens` | ✅ activa | Fractones: earn/burn automático, misiones, arquitectura Hotmart packs |
| `practitioners` | 🔶 parcial | Vistas básicas para perfiles temporales de clientes |
| `reports` | ⬜ vacía | Reportes agregados por usuario / perfil |

## Modelos clave

### `psychometrics.Test`
```python
name, slug, dimension, instrument_type (clinical/adapted/custom),
description, instructions, estimated_minutes, token_cost, active, order
```

### `psychometrics.Question`
```python
test (FK), text, dimension_key, scale, reverse_scored, order
```
Escalas: `likert5` (freq 1-5) · `likert5a` (acuerdo 1-5) · `likert4` (0-4) · `likert3` (0-3) · `likert7` (1-7) · `binary`

### `psychometrics.TestResult`
```python
user (FK, nullable), temp_profile (FK → practitioners.TemporaryProfile, nullable),
test (FK), raw_scores (JSON), evaluation (JSON), ai_insight (text), completed_at
```

### `accounts.UserProfile`
```python
user (OneToOne), plan (free/navegante/practicante/empresa),
map_aesthetic (cosmos/mandala/archipielago/arbol),  # controla el fondo visual
hotmart_subscriber_code, tokens_last_renewed,
onboarding_entry_point, onboarding_noise_area, onboarding_nucleo (JSON), ...
```

### `tokens.TokenBalance`
```python
user (OneToOne), permanent (int), monthly (int), monthly_last_renewed (date)
# permanent = ganados + comprados, nunca expiran
# monthly   = recarga del plan, se reemplaza cada ciclo
# balance   = permanent + monthly (property)
# .spend(amount, reason)         → descuenta monthly primero, luego permanent
# .credit_permanent(amount, reason)
# .credit_monthly(amount, reason)
```

### `tokens.Mission` / `tokens.MissionCompletion`
```python
Mission: slug, name, fracton_reward, order, active
MissionCompletion: user (FK), mission (FK)  # unique_together → idempotente
```

## Reverse scoring (`views.py`)
```python
if q.scale in ('likert5', 'likert5a'): score = 6 - score
if q.scale == 'likert4':               score = 4 - score
if q.scale == 'likert3':               score = 3 - score
if q.scale == 'likert7':               score = 8 - score
if q.scale == 'binary':                score = 1 - score
```

## Los 35 tests
**clinical (7):** Big Five BFI-44, GAD-7, PHQ-9, PSS-10, TAS-20, Dirty Dozen, SVI  
**adapted (17):** Jung, DERS-16, MAIA, PSQI, ECR, IBI, Logo-Test, SWB, Cloninger, VIA, RIASEC, MWQ, MOS-SSS, Kolb, CEQ, SOC-29, Neurosensorial  
**custom (11):** Eneagrama, Heridas Bourbeau, Autosabotaje, Chakras, DRI, DLQ, CIQ, Rueda de la Vida, MAQ, FSS, Fortalezas Prosociales

## Migraciones aplicadas
- `accounts` 0001–0007 (última: alter_map_aesthetic_label → "Cósmico")
- `tokens` 0001–0002 (última: fractones_and_missions)
- `psychometrics` 0001–0004

## Sistema visual — Fondo cósmico + Cuarzo

### Arquitectura del fondo
El fondo Three.js (agujero negro Kepleriano) está ligado al `map_aesthetic` del usuario:
- `cosmos` → agujero negro + partículas (activo)
- `mandala`, `archipielago`, `arbol` → aún sin fondo específico (futuro)

El contexto `map_aesthetic` se inyecta globalmente via:
`accounts/context_processors.py` → registrado en `settings.TEMPLATES[*].context_processors`

`<body data-aesthetic="{{ map_aesthetic|default:'cosmos' }}">` — el módulo JS lo lee y sale si no es cosmos.

### Cuarzo — tratamiento visual de paneles
Todos los templates tienen fondo sólido oscuro sobre el agujero negro:
```css
background: rgba(0,0,0,0.88);
border: 1px solid rgba(255,255,255,0.14–0.16);
border-radius: 20px;
```
Aplicado a: `.auth-box`, `.dash`, `.mapa-hero`, `.entry-card`, `.take-wrap`, `.question-block`, `.list-wrap`, `.perfil-wrap`, `.mapa-page`, `.birth-wrap`, `.lectura-wrap`, `.hd-wrap`, `.saju-wrap`, `.astral-wrap`, `.dim-pill`, etc.

### SPA Navigation
- `spaGo()` en base.html hace fetch + swap de `#page-content`
- Al navegar, también swapea los `<style>` del `{% block extra_head %}` de la nueva página
- Estilos globales marcados con `data-global` (nunca se eliminan)
- Estilos de página inyectados con `data-page-style` (se reemplazan en cada nav)

### Presets del fondo por sección
```javascript
const PRESETS = {
  desktop: {
    onboarding: { bhr:4.0, density:0.32, sizeMult:0.90, bloom:6.0, speedInner:3.05, speedOuter:0.05, camZ:149, camAng:4  },
    general:    { bhr:4.0, density:0.32, sizeMult:1.80, bloom:6.0, speedInner:3.05, speedOuter:0.05, camZ:149, camAng:16 },
    espejo:     { bhr:4.0, density:0.32, sizeMult:2.40, bloom:6.0, speedInner:3.05, speedOuter:0.05, camZ:149, camAng:85 },
  },
  mobile: {
    onboarding: { bhr:12.4, density:0.67, sizeMult:1.40, bloom:6.0, speedInner:1.95, speedOuter:0.00, camZ:200, camAng:11 },
    general:    { bhr:12.4, density:1.00, sizeMult:2.15, bloom:6.0, speedInner:1.95, speedOuter:0.00, camZ:116, camAng:22 },
    espejo:     { bhr:12.4, density:0.62, sizeMult:2.60, bloom:4.0, speedInner:1.95, speedOuter:0.00, camZ:200, camAng:85 },
  },
}
```

## Sistema de Fractones

### Economía
| Plan | Fractones/mes (expiran) |
|------|------------------------|
| free | 100 |
| navegante ($10) | 600 |
| practicante ($39) | 3.000 |

### Costos (TOKEN_COSTS en settings)
```python
'espejo_exchange': 4    # 1 mensaje + respuesta
'ai_insight':      20
'report':          30
```

### Ganancias automáticas (FRACTON_REWARDS)
```python
'test_completed':      8   # signal post_save TestResult
'dimension_completed': 25  # bonus al completar toda una dimensión
'streak_weekly':       15  # ≥3 tests en 7 días, 1 vez/semana
```

### Misiones (fracton_reward acreditado una sola vez)
| slug | recompensa |
|------|-----------|
| `onboarding` | +60 |
| `first_test` | +20 |
| `first_espejo` | +40 |
| `first_dimension` | +50 |

### API pública (`tokens/service.py`)
```python
from tokens.service import spend, has_balance, credit_mission, renew_monthly

spend(user, 'espejo_exchange')   # True/False — descuenta y registra
has_balance(user, 'ai_insight')  # True/False — sin descontar
credit_mission(user, 'first_espejo')  # idempotente
```

### Hotmart packs (arquitectura lista, pendiente configurar vars)
```python
# .env Railway:
HOTMART_PACK_200   = offer_code_del_pack_200_fractones
HOTMART_PACK_600   = offer_code_del_pack_600_fractones
HOTMART_PACK_2000  = offer_code_del_pack_2000_fractones
```
El webhook en `/tokens/hotmart-webhook/` detecta automáticamente si el offer es pack o suscripción.

### Cron Railway
```bash
python3 manage.py renew_monthly_fractones   # día 1 de cada mes
```

## CSS / Design system (`templates/base.html`)
Paleta actual "Espejo" (dark, teal):
```css
--bg: #000000;  --surface: #111118;  --surface2: #1a1a26;
--border: #2a2a3a;  --text: #e2e2f0;  --muted: #7070a0;
--accent: #4ecdc4;  --accent2: #7c6dfa;
--luz-intensa: #f0c040;  --luz: #4ecdc4;  --transicion: #f4a035;
--sombra: #7c6dfa;  --sombra-dom: #e05050;
```

Badge classes: `badge-validado` (teal) · `badge-adaptado` (amber) · `badge-endonauta` (purple)  
Polarity bars: `bar-luz-intensa` · `bar-luz` · `bar-transicion` · `bar-sombra` · `bar-sombra-dominante`

## Archivos clave
- `accounts/context_processors.py` — inyecta `map_aesthetic` en todos los templates
- `tokens/service.py` — API pública de fractones (spend/credit/missions)
- `tokens/signals.py` — earn automático al completar tests
- `tokens/hotmart.py` — webhook: suscripciones + packs
- `psychometrics/evaluator.py` — lógica de evaluación por test, dispatcher, polaridad sombra/luz
- `psychometrics/management/commands/seed_tests.py` — seed de los 35 tests
- `templates/base.html` — CSS global, SPA nav, Three.js cosmos, context processor hook
- `templates/psychometrics/test_take.html` — formulario de respuesta con progress bar
- `templates/psychometrics/test_result.html` — resultados con barras de polaridad
- `templates/psychometrics/test_list.html` — grid de tests por dimensión

## Sistema visual — Mapa Interior Mandala ✅

### Fondo mandala (aesthetic=mandala)
- Canvas 2D `#mandala-bg` en base.html — se muestra solo cuando `map_aesthetic='mandala'`
- Three.js cosmos cede el paso via `AESTHETIC_HAS_OWN_BG = { mandala: true }`
- Presets por sección (igual que cosmos), cambian automáticamente con SPA via evento `bg:preset`:

| Sección | Simetría | Paleta | Velocidad | Alpha |
|---------|----------|--------|-----------|-------|
| tests / psychometrics | 6 | arcano (dorado) | 1.20 | 40% |
| birth / nacimiento | 3 | blanco | 0.45 | 70% |
| onboarding / login | 3 | blanco | 0.45 | 70% |
| espejo / mirror | 4 | blanco | 0.95 | 40% |
| general (resto) | 6 | arcano | 1.20 | 40% |

- Zoom global: 1.84. Sin controles UI — configuración hardcodeada.
- Configurador standalone en `/home/nikka/Proyectos/mandala.html` — tiene botón "Copiar Configuración" que pega JSON con todos los parámetros.

### Cuarzo aplicado (paneles rgba(0,0,0,0.88))
Todos los templates tienen cuarzo: auth, dashboard, test_take/list/result, my_results, perfil, mapa_interior, birth/*, reports/dashboard.

## Pendientes (en orden de prioridad)

### Conectar fractones en features existentes
1. **Espejo de Conflictos** — añadir `spend(user, 'espejo_exchange')` en la view antes del API call + `credit_mission(user, 'first_espejo')` en primera sesión
2. **AI Insights** — añadir `spend(user, 'ai_insight')` antes de llamar DeepSeek en `test_result`
3. **`credit_mission(user, 'onboarding')`** — disparar al final del onboarding_viaje

### Espejo de Conflictos (`mirror` app)
4. Views AJAX, template conversación, burbuja flotante en base.html

### UI / Visual
5. **Mapa Interior — fondos árbol y archipiélago** — pendientes (mandala ✅ ya implementado)
6. **Eliminar theme switcher temporal** de `base.html` y hardcodear paleta definitiva

### Hotmart packs
7. Crear los 3 productos pack en Hotmart, agregar offer codes a Railway env vars, testear webhook end-to-end

### Otras features
8. **Practitioners views** — gestionar perfiles de clientes, asignar tests, ver resultados
9. **Reportes** (`reports` app) — dashboard agregado con evolución temporal
10. **Personalización de paleta** desde perfil de usuario

### Instrumentos a auditar (implementación incompleta)
11. **ECR** — actualmente ~10 ítems; debería ser ECR-R (36) o ECR-12 escala likert7
12. **SOC-29/SOC-13** — actualmente 7 ítems; SOC-29 tiene 29 ítems bipolar likert7
13. **MAIA** — actualmente 21 ítems; MAIA-2 tiene 37 ítems escala 0-5
14. **DERS-16** — actualmente 8 ítems; versión validada tiene 16 ítems likert5
15. **PSQI** — suma simple; scoring real tiene 7 componentes con ponderación diferente

## Notas metodológicas importantes
- Los tests `clinical` usan ítems exactos de instrumentos validados en español
- Los tests `adapted` usan el instrumento como referencia con ítems o número diferente — **siempre mostrar disclaimer**
- Los tests `custom` son herramientas de reflexión endonauta — **no son diagnóstico**
- Los resultados clínicos se presentan con interpretación estándar + lectura endonauta (sombra/luz) como capa adicional
- BDI-II → reemplazado por PHQ-9 (libre de copyright, Kroenke & Spitzer 2001)
- SD3 → reemplazado por Dirty Dozen (Jonason & Webster 2010, 12 ítems)
