# MirrorWork — Instrucciones para Claude

## Comando siempre: `python3 manage.py` (nunca `python`)

## Stack
- Django 6, SQLite (dev), Railway (deploy target)
- WhiteNoise para static files
- DeepSeek API (key en `.env`) para AI insights
- No git todavía (pendiente `git init`)

## Arrancar el servidor
```bash
python3 manage.py runserver 8001
python3 manage.py seed_tests --force   # recarga los 35 tests
python3 manage.py migrate
```

## Estructura de apps
| App | Estado | Descripción |
|-----|--------|-------------|
| `accounts` | ✅ activa | User (AbstractUser, email como USERNAME_FIELD), login/register/dashboard |
| `psychometrics` | ✅ activa | Tests, preguntas, resultados, evaluador, seed |
| `mirror` | 🔶 en progreso | KB lista (40 docs, 97 chunks, 43 autores). Falta: views, templates, burbuja flotante |
| `practitioners` | ⬜ vacía | Vistas para gestionar perfiles temporales de clientes |
| `reports` | ⬜ vacía | Reportes agregados por usuario / perfil |
| `tokens` | ⬜ vacía | Sistema de tokens para acceso a features premium |

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
- `0001_initial`
- `0002_add_likert3_scale`
- `0003_add_likert5a_scale`
- `0004_add_instrument_type`

## CSS / Design system (`templates/base.html`)
Paleta actual "Espejo" (dark, teal):
```css
--bg: #08080f;  --surface: #111118;  --surface2: #1a1a26;
--border: #2a2a3a;  --text: #e2e2f0;  --muted: #7070a0;
--accent: #4ecdc4;  --accent2: #7c6dfa;
--luz-intensa: #f0c040;  --luz: #4ecdc4;  --transicion: #f4a035;
--sombra: #7c6dfa;  --sombra-dom: #e05050;
```
Paletas alternativas definidas en el theme switcher (TEMPORAL — ver pendientes):
- **Endonautas** (warm gold): accent=#c8a855, bg=#0b0906
- **Abismo** (deep blue): accent=#4488ee, bg=#060810
- **Crepúsculo** (rose): accent=#d46fa0, bg=#0d080e

Badge classes: `badge-validado` (teal) · `badge-adaptado` (amber) · `badge-endonauta` (purple)  
Polarity bars: `bar-luz-intensa` · `bar-luz` · `bar-transicion` · `bar-sombra` · `bar-sombra-dominante`

## Archivos clave
- `psychometrics/evaluator.py` — lógica de evaluación por test, dispatcher, polaridad sombra/luz
- `psychometrics/management/commands/seed_tests.py` — seed de los 35 tests con ítems validados
- `templates/base.html` — CSS global, nav, theme switcher temporal
- `templates/psychometrics/test_take.html` — formulario de respuesta con progress bar
- `templates/psychometrics/test_result.html` — visualización de resultados con barras de polaridad
- `templates/psychometrics/test_list.html` — grid de tests por dimensión

## Pendientes (en orden de prioridad)

### UI / Visual
1. **Mejorar visual de `test_take.html`** — poco contraste en opciones de escala, fuentes mal dimensionadas, opciones difíciles de distinguir al responder
2. **Decidir paleta definitiva** y eliminar el bloque `<!-- THEME SWITCHER TEMPORAL -->` de `base.html`, hardcodear los valores en `:root`

### Features
3. **Espejo de Conflictos** (`mirror` app) — ✅ modelos MirrorDocumento/MirrorChunk + ConflictSession. ✅ KB seed (40 docs, 97 chunks). ✅ index_mirror_docs (requiere OPENAI_API_KEY). Pendiente: views AJAX, template conversación, burbuja flotante en base.html
4. **Practitioners views** (`practitioners` app) — crear y gestionar perfiles temporales de clientes, asignarles tests, ver sus resultados
5. **Sistema de tokens** (`tokens` app) — acceso a features premium (AI insights, Espejo)
6. **Reportes** (`reports` app) — dashboard agregado por usuario con evolución en el tiempo
7. **Personalización de colores en panel de usuario** — permitir al usuario elegir su paleta preferida desde su perfil (usar las mismas variables CSS del theme switcher temporal)
8. **AI Insights con DeepSeek** — generar `ai_insight` en `TestResult` tras completar un test

### Instrumentos a auditar (implementación incompleta)
9. **ECR** — actualmente ~10 ítems; debería ser ECR-R (36 ítems) o ECR-12 (12 ítems validados), escala likert7
10. **SOC-29/SOC-13** — actualmente 7 ítems; SOC-29 tiene 29 ítems bipolar likert7, o usar SOC-13 (versión corta validada)
11. **MAIA** — actualmente 21 ítems likert5; MAIA-2 tiene 37 ítems escala 0-5
12. **DERS-16** — actualmente 8 ítems custom; DERS-16 es la versión validada con 16 ítems likert5
13. **PSQI** — actualmente suma simple; scoring real tiene 7 componentes con ponderación diferente por ítem

### DevOps
14. **`git init` + push a GitHub**
15. **Deploy a Railway** (Procfile ya existe, añadir `runtime.txt` con versión de Python)

## Notas metodológicas importantes
- Los tests `clinical` usan ítems exactos de instrumentos validados en español
- Los tests `adapted` usan el instrumento como referencia pero con ítems o número de preguntas diferente — **siempre mostrar disclaimer** de que son orientativos
- Los tests `custom` son herramientas de reflexión endonauta — **no son diagnóstico**
- Los resultados clínicos se presentan primero con la interpretación estándar del instrumento, y encima la lectura endonauta (sombra/luz) como capa adicional
- BDI-II fue reemplazado por PHQ-9 (libre de copyright, validado en español, Kroenke & Spitzer 2001)
- SD3 fue reemplazado por Dirty Dozen (Jonason & Webster 2010, 12 ítems, 4 por factor)
