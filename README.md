# MirrorWork

Plataforma de psicometría endonauta con IA. Permite a usuarios explorar su mundo interior a través de 35 tests validados, un asistente conversacional (Espejo de Conflictos), lecturas de IA y gestión de perfiles de clientes para practicantes.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Django 6, Python 3.12 |
| Base de datos | SQLite (dev) · PostgreSQL via `dj-database-url` (prod) |
| IA / Chat | DeepSeek API (`deepseek-chat`) |
| Embeddings RAG | OpenAI `text-embedding-3-small` (opcional) |
| Static files | WhiteNoise + CompressedManifestStaticFilesStorage |
| Deploy | Railway (Nixpacks) |
| Pagos | Hotmart (webhooks) |

---

## Apps

| App | Ruta URL | Descripción |
|-----|----------|-------------|
| `accounts` | `/accounts/` | Usuarios (AbstractUser, email como USERNAME_FIELD), registro, login, dashboard, perfil con plan |
| `psychometrics` | `/psicometria/` | 35 tests, preguntas, evaluador, resultados con lecturas de IA |
| `mirror` | `/espejo/` | KB de 40 docs / 97 chunks, chat AJAX con DeepSeek, RAG por embedding o keyword |
| `practitioners` | `/practicantes/` | Perfiles temporales de clientes, tokens asignados, enlace de acceso UUID |
| `tokens` | `/tokens/` | Balance, historial de transacciones, planes, webhook Hotmart |
| `reports` | `/reportes/` | Dashboard de progreso por usuario y dimensión |

---

## Los 35 tests

**Clínicos (7):** Big Five BFI-44, GAD-7, PHQ-9, PSS-10, TAS-20, Dirty Dozen, SVI

**Adaptados (17):** Jung, DERS-16, MAIA, PSQI, ECR, IBI, Logo-Test, SWB, Cloninger, VIA, RIASEC, MWQ, MOS-SSS, Kolb, CEQ, SOC-29, Neurosensorial

**Endonautas (11):** Eneagrama, Heridas Bourbeau, Autosabotaje, Chakras, DRI, DLQ, CIQ, Rueda de la Vida, MAQ, FSS, Fortalezas Prosociales

---

## Planes de suscripción

| Plan | Tokens/mes | Perfiles clientes | Precio |
|------|-----------|-------------------|--------|
| Free | 50 (solo al registro) | 0 | Gratis |
| Navegante | 400 | 0 | $10 USD/mes |
| Practicante | 600 | 10 | $39 USD/mes |
| Empresa | 9999 | 999 | Personalizado |

Los planes se activan automáticamente vía webhook de Hotmart al confirmar el pago.

---

## Costos de tokens

| Feature | Tokens |
|---------|--------|
| Tests psicométricos | Gratis |
| Lectura del Espejo (AI insight en resultado) | 5 |
| Mensaje en Espejo de Conflictos | 10 |
| Generar reporte | 3 |

---

## Instalación local

```bash
git clone <repo>
cd mirrorwork
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # editar con tus keys
python3 manage.py migrate
python3 manage.py seed_tests
python3 manage.py seed_mirror_kb
python3 manage.py runserver 8001
```

### Variables de entorno requeridas (`.env`)

```env
SECRET_KEY=genera-una-key-larga-aleatoria
DEBUG=True

# Base de datos (Railway inyecta esto automáticamente en prod)
# DATABASE_URL=postgresql://...

# IA
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-proj-...   # opcional, para embeddings RAG

# Hotmart (configurar después de crear productos)
HOTMART_WEBHOOK_TOKEN=token-generado-por-hotmart
HOTMART_PRODUCT_ID_NAVEGANTE=123456
HOTMART_PRODUCT_ID_PRACTICANTE=789012
HOTMART_CHECKOUT_NAVEGANTE=https://pay.hotmart.com/XXXXX
HOTMART_CHECKOUT_PRACTICANTE=https://pay.hotmart.com/YYYYY

# Railway (auto-inyectado en prod)
# RAILWAY_PUBLIC_DOMAIN=mirrorwork.up.railway.app
# ALLOWED_HOSTS=mirrorwork.up.railway.app
```

---

## Comandos de gestión

```bash
# Cargar / recargar los 35 tests
python3 manage.py seed_tests
python3 manage.py seed_tests --force   # borra y regenera todo

# Cargar / recargar la KB del Espejo (40 docs, 97 chunks)
python3 manage.py seed_mirror_kb
python3 manage.py seed_mirror_kb --force

# Generar embeddings para RAG (requiere OPENAI_API_KEY)
python3 manage.py index_mirror_docs
python3 manage.py index_mirror_docs --force   # re-indexa todo
```

---

## Deploy en Railway

### 1. Crear proyecto en Railway y añadir PostgreSQL

Railway inyecta `DATABASE_URL` automáticamente al conectar el plugin de Postgres.

### 2. Variables de entorno en Railway

```env
SECRET_KEY=<genera con: python -c "import secrets; print(secrets.token_urlsafe(50))">
DEBUG=False
ALLOWED_HOSTS=tu-app.up.railway.app
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-proj-...
HOTMART_WEBHOOK_TOKEN=...
HOTMART_PRODUCT_ID_NAVEGANTE=...
HOTMART_PRODUCT_ID_PRACTICANTE=...
HOTMART_CHECKOUT_NAVEGANTE=...
HOTMART_CHECKOUT_PRACTICANTE=...
```

### 3. El `Procfile` ejecuta en orden al hacer deploy:
```
migrate → seed_tests → seed_mirror_kb → collectstatic → gunicorn
```

### 4. Configurar webhook en Hotmart

URL del webhook: `https://tu-app.up.railway.app/tokens/hotmart-webhook/`

Eventos a suscribir: `PURCHASE_APPROVED`, `PURCHASE_CANCELED`, `PURCHASE_REFUNDED`, `PURCHASE_CHARGEBACK`, `SUBSCRIPTION_CANCELLATION`

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

### KB del Espejo

40 documentos / 97 chunks en 3 categorías:
- `ebook` — fundamentos de Endonautica y ley espejo
- `marco_teorico` — 28 autores (Jung, Gestalt, NLP, IFS, Somatic, Bourbeau, etc.)
- `tradicion` — 6 sistemas (Eneagrama, Human Design, Chakras, Astrología, etc.)

---

## Modelos clave

### `accounts.UserProfile`
```python
plan: 'free' | 'navegante' | 'practicante' | 'empresa'
plan_active_since: DateField
hotmart_subscriber_code: CharField  # código de suscriptor Hotmart
```

### `tokens.TokenBalance`
```python
user: OneToOneField
balance: IntegerField
spend(amount, reason) → bool   # False si saldo insuficiente
credit(amount, reason)
```

### `mirror.ConflictSession`
```python
user, title, conflict_description
messages: JSONField  # lista de {role, content}
status: 'active' | 'archived'
add_message(role, content)
```

### `practitioners.TemporaryProfile`
```python
created_by, alias, notes
token_allocation, tokens_used
access_code: UUIDField   # UUID único para enlace de acceso
active: bool
```

---

## Design system

Paleta "Espejo" (dark teal):
```css
--bg: #08080f          --surface: #111118      --surface2: #1a1a26
--border: #2a2a3a      --text: #e2e2f0         --muted: #7070a0
--accent: #4ecdc4      --accent2: #7c6dfa
--luz-intensa: #f0c040 --luz: #4ecdc4          --transicion: #f4a035
--sombra: #7c6dfa      --sombra-dom: #e05050
```

---

## Notas metodológicas

- Tests `clinical` usan ítems exactos de instrumentos validados en español
- Tests `adapted` son orientativos — se muestra disclaimer automáticamente
- Tests `custom` son herramientas de reflexión endonauta — no son diagnóstico
- Las "lecturas del Espejo" (AI insights) nunca diagnostican, devuelven la conciencia al interior
- BDI-II reemplazado por PHQ-9 (libre de copyright, Kroenke & Spitzer 2001)
- SD3 reemplazado por Dirty Dozen (Jonason & Webster 2010)
