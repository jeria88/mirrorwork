# MirrorWork — app.endonautas.cl

App de autoconocimiento profundo. 35 tests psicométricos, Espejo de Conflictos (IA conversacional), lecturas de nacimiento (carta astral, Human Design, Saju), comunidad y sistema de fractones.

**Producción:** https://app.endonautas.cl — live ✅

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Django 6, Python 3.12 |
| Base de datos | SQLite (dev) · PostgreSQL via `dj-database-url` (prod) |
| IA / Chat | DeepSeek API (`deepseek-chat`) |
| Embeddings RAG | OpenAI `text-embedding-3-small` (opcional) |
| Static files | WhiteNoise + CompressedManifestStaticFilesStorage |
| Deploy | Railway (Nixpacks) |
| Pagos | Hotmart (webhooks) |

---

## Apps

| App | URL | Descripción |
|---|---|---|
| `accounts` | `/` | Usuario (AbstractUser, email como USERNAME_FIELD), login/register/dashboard, mapa interior, perfil, onboarding |
| `psychometrics` | `/psicometria/` | 35 tests, evaluador de polaridades, lecturas de IA (DeepSeek) |
| `mirror` | `/espejo/` | KB con RAG (40 docs, 97 chunks), chat AJAX con DeepSeek, memorias del Espejo |
| `birth` | `/nacimiento/` | Carta Astral, Human Design, Saju — lecturas endonautas generadas por IA |
| `community` | `/comunidad/` | Feed, SharedInsights (compartir resultados/sesiones), reacciones, comentarios, follows |
| `tokens` | `/tokens/` | Fractones — balance, historial, misiones, webhook Hotmart |
| `background` | `/fondos/` | Generador de fondos: cosmos (Three.js), mandala (Canvas 2D), psicodélico |
| `practitioners` | `/practitioners/` | Perfiles temporales de clientes para facilitadores |
| `reports` | `/reportes/` | Dashboard de progreso por dimensión |
| `sensorial` | `/sensorial/` | Ejercicios sensoriales (respiración guiada) |
| `vr` | `/vr/` | MirrorWork VR — staff only |
| `studio` | `/cgm/` | Content Studio / CGM — Editor y previsualización de Reels y Carruseles generados (staff only) |

---

## Los 35 tests

**Clínicos (7):** BFI-44, GAD-7, PHQ-9, PSS-10, TAS-20, Dirty Dozen, SVI

**Adaptados (17):** Jung, DERS-16, MAIA, PSQI, ECR, IBI, Logo-Test, SWB, Cloninger, VIA, RIASEC, MWQ, MOS-SSS, Kolb, CEQ, SOC-29, Neurosensorial

**Endonautas (11):** Eneagrama, Heridas Bourbeau, Autosabotaje, Chakras, DRI, DLQ, CIQ, Rueda de la Vida, MAQ, FSS, Fortalezas Prosociales

---

## Sistema de Fractones

| Plan | Fractones/mes | Precio |
|---|---|---|
| Free | 100 | Gratis |
| Navegante | 600 | $10 USD/mes |
| Practicante | 3.000 | $39 USD/mes |

| Feature | Costo |
|---|---|
| Tests psicométricos | Gratis |
| Mensaje en el Espejo | 4 fractones |
| Lectura de IA (test insight) | 20 fractones |
| Generar reporte | 30 fractones |

Misiones de onboarding que acreditan fractones: `onboarding` (+60), `first_test` (+20), `first_espejo` (+40), `first_dimension` (+50).

---

## Blog — postulación de contenido

Los usuarios pueden postular contenido al blog editorial (`endonautas.cl/blog/`) directamente desde la app:

- **Espejo**: botón "Postular al blog" en el header del chat (sesiones con mensajes)
- **Tests**: botón en el action-row del resultado
- **Lecturas de nacimiento**: botón debajo de las secciones reveladas

El modal se abre inline, pre-rellena el contenido desde la fuente, el usuario edita y envía para revisión. La revisión y publicación ocurre en `endonautas.cl/django-admin/`.

---

## Design system

Paleta "Espejo" (dark):
```css
--bg: #000000          --surface: #111118      --surface2: #1a1a26
--border: #2a2a3a      --text: #e2e2f0         --muted: #7070a0
--accent: #4ecdc4      --accent2: #7c6dfa
--luz-intensa: #f0c040 --luz: #4ecdc4          --transicion: #f4a035
--sombra: #7c6dfa      --sombra-dom: #e05050
```

Fondos dinámicos: cosmos (agujero negro Three.js kepleriano), mandala (Canvas 2D paramétrico), psicodélico (Canvas 2D con transiciones de escena). Controlados por `UserProfile.map_aesthetic`.

---

## Arquitectura del Espejo de Conflictos

```
Usuario escribe mensaje
        ↓
_retrieve_context(mensaje)
  ├─ si hay embeddings → cosine similarity sobre MirrorChunk
  └─ si no → keyword overlap fallback
        ↓
_get_test_summary(user)   ← resultados de tests del usuario
        ↓
_call_deepseek(historial[-12:], kb_chunks + test_summary)
        ↓
ConflictSession.add_message("assistant", respuesta)
        ↓
JsonResponse → frontend AJAX
```

KB: 40 documentos / 97 chunks — categorías `ebook`, `marco_teorico` (28 autores), `tradicion` (6 sistemas).

---

## Instalación local

```bash
git clone <repo>
cd mirrorwork
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env  # editar con tus keys
python3 manage.py migrate
python3 manage.py seed_tests --force
python3 manage.py seed_missions
python3 manage.py seed_mirror_kb
python3 manage.py runserver 8001
```

### Variables de entorno

```env
SECRET_KEY=
DEBUG=True
DATABASE_URL=               # Railway inyecta en prod
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-proj-...  # opcional, para embeddings RAG
HOTMART_WEBHOOK_TOKEN=
HOTMART_PRODUCT_ID_NAVEGANTE=
HOTMART_PRODUCT_ID_PRACTICANTE=
HOTMART_CHECKOUT_NAVEGANTE=
HOTMART_CHECKOUT_PRACTICANTE=
```

---

## Deploy (Railway)

El despliegue está configurado mediante Nixpacks, utilizando el script de inicio [scripts/start.sh](file:///home/nikka/Proyectos/endonautas/mirrorwork/scripts/start.sh). 

#### Ciclo de arranque del Contenedor:
1. `prepare_db` y `migrate --fake-initial` (Django migrations).
2. Migración de datos heredados (`migrate_mirrorwork_data`).
3. Sincronización de base de datos a JSON del Content Studio (`sync_cgm_to_studio`).
4. Inicialización de seeds (Wagtail, Centro, Misiones, Tests, KB, etc.).
5. Recopilación de estáticos (`collectstatic`).
6. Ejecución en background del servidor Express del Content Studio (`node studio/server.mjs &`).
7. Ejecución principal de Gunicorn (`gunicorn config.wsgi`).

#### Persistencia (Railway Volumes):
El sistema de archivos de Railway es efímero. Para asegurar la persistencia del Content Studio, se deben crear y montar los siguientes volúmenes en el dashboard de Railway:

- `/app/studio/data` — Datos de configuración y base de datos local JSON (Reels, Carruseles y estados).
- `/app/contenido/carruseles/pngs` — Directorio de imágenes generadas para carruseles.
- `/app/contenido/reels/mp4` — Directorio de videos MP4 generados para reels.
- `/app/contenido/reels/scripts` — Directorio de transcripciones y scripts generados.

Webhook Hotmart: `https://app.endonautas.cl/tokens/hotmart-webhook/`

Eventos: `PURCHASE_APPROVED`, `PURCHASE_CANCELED`, `PURCHASE_REFUNDED`, `PURCHASE_CHARGEBACK`, `SUBSCRIPTION_CANCELLATION`

---

## Cross-site

La barra superior de `base.html` enlaza hacia el ecosistema editorial:
- `endonautas.cl/endonautica/` — el libro fundacional
- `endonautas.cl/equipo/` — misión, visión, comunidad

Las rutas `/mision/` y `/comunidad/` ya no existen en platform — apuntar siempre a `/equipo/`.

---

## Notas metodológicas

- Tests `clinical`: ítems exactos de instrumentos validados en español
- Tests `adapted`: orientativos — se muestra disclaimer automáticamente
- Tests `custom`: herramientas de reflexión endonauta — no son diagnóstico
- PHQ-9 reemplaza BDI-II (libre de copyright). Dirty Dozen reemplaza SD3.
