# Endonautas — Hoja de ruta de negocio
*Generado: 2026-05-26*

---

## Posicionamiento

**Visión (Franco):** Para alguien que ha probado todo para alcanzar su mejor versión o sanar, menos ir para adentro, y quiere aumentar su nivel de conciencia y entenderse a sí mismo de verdad para tomar acción hacia sus metas.

**Puerta de entrada (mercado):** Para alguien en un conflicto que no entiende, que quiere una forma de mirarlo sin tener que pagar sesiones de terapia.

> Las dos son verdad. La primera es la visión del producto. La segunda es el dolor inmediato que lleva a buscar.

---

## Los cuatro flujos de ingreso

| Flujo | Modelo | Proyección conservadora (mes 24-36) |
|---|---|---|
| Suscripciones individuales | $12/mes (navegante) · $39/mes (practicante) | $2.400/mes (200 usuarios) |
| Practicantes | $30/mes por cuenta | $1.200/mes (40 practicantes) |
| Cohortes "Viaje Endonauta" | $150-200 por participante | ~$900/mes promedio |
| Formación de Facilitadores | $600-900 por certificación | ~$875/mes promedio |
| **Total estimado** | | **~$5.400/mes** |

---

## Secuencia general

```
Mes 1-3    │ FUNDAMENTOS     │ Espejo + fondo dinámico + 10 usuarios
Mes 3-6    │ VALIDACIÓN      │ Practicantes + funnel ebook + contenido
Mes 6-12   │ TRACCIÓN v1     │ Primera cohorte + SEO + primeros $100 ads
Mes 12-18  │ TRACCIÓN v2     │ 20 practicantes + cohortes regulares + ads retargeting
Mes 18-36  │ ESCALA          │ Certificación + ads fríos + 4 flujos activos
```

---

## ETAPA 0 — Fundamentos
### Mes 1 al 3 · Objetivo: que el producto cumpla su promesa central

---

### 0.A · Producto — el ciclo mínimo que tiene que funcionar

**Espejo de Conflictos**
- [ ] Construir view AJAX con endpoint `/espejo/sesion/`
- [ ] Template de conversación: burbuja flotante + historial de mensajes
- [ ] Conectar `spend(user, 'espejo_exchange')` antes del call a DeepSeek
- [ ] Primera sesión gratuita sin costo de fractones (para usuarios nuevos)
- [ ] Cierre de sesión: guardar patrón revelado + pregunta de cierre
- [ ] `credit_mission(user, 'first_espejo')` al completar primera sesión

**Fondo dinámico**
- [ ] Definir 3-4 parámetros visuales que mapean a dimensiones de tests (sombra alta → más densidad, luz alta → más brillo)
- [ ] Función que calcula esos parámetros desde los TestResult del usuario
- [ ] El fondo actualiza automáticamente cuando se completa un test nuevo
- [ ] Opción de capturar/exportar el fondo como imagen estática (para compartir)

**Onboarding**
- [ ] `credit_mission(user, 'onboarding')` al final del último paso
- [ ] El onboarding termina con el fondo renderizado — no con un dashboard vacío
- [ ] Sugerencia de "primer test" basada en respuestas del onboarding

**Seguridad clínica**
- [ ] PHQ-9 ≥ 20 → mensaje diferente + link a recursos (MINSAL Chile)
- [ ] GAD-7 ≥ 15 → mismo tratamiento
- [ ] Disclaimer visible en tests clínicos y adaptados antes de empezar

**Infraestructura**
- [ ] Configurar email real en Railway (Brevo SMTP) — reset de contraseña funcional
- [ ] `spend(user, 'ai_insight')` mover a antes de llamar DeepSeek
- [ ] Wiring de `sensorial` URLs en `config/urls.py`

---

### 0.B · Negocio — estructura antes de vender

- [ ] Definir los 3 planes con sus beneficios en lenguaje de usuario (no técnico)
- [ ] Crear productos en Hotmart: Navegante + Practicante + 3 packs fractones
- [ ] Página de precios en `app.endonautas.cl/precios/`
- [ ] Términos de uso y política de privacidad (mínimo legal Chile)
- [ ] Documento interno: qué incluye la cuenta de practicante

---

### 0.C · Contenido y RRSS — instalar el hábito, no crecer todavía

**Plataformas activas:** Instagram + LinkedIn (solo estas dos)

**Frecuencia mínima:**
- Instagram: 3 posts/semana (2 carruseles + 1 reel o story)
- LinkedIn: 1 post/semana

**Formatos a probar:**
- Carrusel: conceptos del libro en 5-7 slides ("¿Qué es la sombra?", "¿Por qué repetís el mismo patrón?")
- Reel corto (30-60 seg): Franco directo a cámara — una pregunta incómoda sin respuesta fácil
- Story: proceso de construcción del producto, behind-the-scenes
- LinkedIn: reflexión sobre uso de instrumentos psicométricos en terapia

**Tareas de configuración:**
- [ ] Bio de Instagram actualizada: quién es Franco, qué es Endonautas, link en bio
- [ ] Destacados en Instagram: Historia, Método, App, Testimonios (vacíos, listos para llenar)
- [ ] Banco de 12 posts creados antes de publicar el primero
- [ ] Definir el tono: primera persona, sin distancia clínica, sin autoayuda superficial

---

### 0.D · Red personal — los primeros 10

- [ ] Identificar 10 personas de la red directa (ex-clientes, colegas, lectores del libro)
- [ ] Invitación personal — no masiva
- [ ] Acompañar el onboarding de cada uno personalmente
- [ ] Conversación de feedback después de la primera semana (llamada, no encuesta)
- [ ] Documentar qué sorprendió, qué confundió, qué frase usaron para describirlo

---

## ETAPA 1 — Validación
### Mes 3 al 6 · Objetivo: probar que el canal practicantes funciona y que el ebook convierte

---

### 1.A · Producto — practicantes mínimo viable

- [ ] Vista para crear/gestionar perfiles de clientes (TemporaryProfiles)
- [ ] Asignación de tests a un perfil de cliente
- [ ] Vista del practicante: ver resultados de sus clientes
- [ ] Acceso del cliente con código único (sin registro completo necesario)
- [ ] Email automático al practicante cuando un cliente completa un test

---

### 1.B · Negocio — activar el canal practicantes

- [ ] Listar 5 terapeutas de confianza de la red de Franco
- [ ] Acceso gratuito durante 2 meses a cambio de feedback detallado
- [ ] Llamada de onboarding con cada uno (30 min)
- [ ] Definir el pitch específico para terapeutas
- [ ] Al mes 2: ofrecer continuidad a $25-30/mes — registrar quién convierte
- [ ] Documentar el caso de uso de cada terapeuta como testimonio

---

### 1.C · Negocio — funnel del ebook

- [ ] Secuencia de 3 emails en Brevo para compradores del ebook:
  - Email 1 (día 3): puente libro → app desde el contenido de un capítulo específico
  - Email 2 (día 7): "El patrón que más repite la gente que leyó el capítulo X" → test relacionado
  - Email 3 (día 14): invitación directa a la app con acceso gratuito
- [ ] Medir: apertura, clic, registro
- [ ] CTA en última página del ebook apuntando a la app

---

### 1.D · Contenido — analizar y ajustar

- [ ] Revisar métricas de los primeros 24 posts: guardados, compartidos, preguntas
- [ ] Duplicar el formato con mejor engagement
- [ ] Primer testimonio visual de los 10 usuarios iniciales (si aceptan)
- [ ] LinkedIn: artículo largo sobre "Por qué los tests psicométricos no alcanzan solos"
- [ ] Story fija en Instagram mostrando el fondo dinámico

---

### 1.E · Comunidad embrión

- [ ] Grupo privado WhatsApp o Discord para los primeros 30-50 usuarios
- [ ] Franco activo: responde preguntas, comparte reflexiones semanales
- [ ] No es soporte técnico — es espacio de práctica del método
- [ ] Objetivo: que los usuarios se hablen entre sí

---

## ETAPA 2 — Tracción
### Mes 6 al 18 · Objetivo: primeros ingresos reales, primera cohorte, SEO activo

---

### 2.A · Producto — profundidad

- [ ] Sistema de recomendación de siguiente test según resultados previos
- [ ] Dashboard personal con evolución de dimensiones en el tiempo
- [ ] Fondo dinámico v2: más parámetros, mayor sensibilidad
- [ ] Opción "compartir mi mundo interior" — imagen del fondo + frase generada
- [ ] Espejo v2: memoria entre sesiones (el espejo recuerda patrones anteriores)

---

### 2.B · Negocio — primera cohorte "Viaje Endonauta"

**Estructura del programa (6 semanas):**
- Semana 1: Onboarding + primer test + primera sesión del Espejo
- Semanas 2-5: Una dimensión por semana + sesión grupal de integración (Zoom)
- Semana 6: Cierre, síntesis del viaje interior, próximos pasos

**Tareas:**
- [ ] Diseñar el currículo semana a semana
- [ ] Precio primera cohorte: $120-150 (objetivo: testimonio, no rentabilidad)
- [ ] Convocatoria: lista Brevo + Instagram + red personal
- [ ] Máximo 15 personas para poder acompañar bien
- [ ] Recopilar 5 testimonios escritos y 2-3 en video post-cohorte

---

### 2.C · Negocio — practicantes en crecimiento

- [ ] Pedir 2 referidos a cada uno de los 5 terapeutas iniciales
- [ ] Onboarding de practicantes documentado — ya no requiere presencia de Franco
- [ ] Webinar mensual gratuito para terapeutas: "Cómo uso Endonautas en sesión"
- [ ] El webinar es captación — los asistentes se registran como practicantes
- [ ] Meta al mes 18: 20-25 practicantes activos pagando

---

### 2.D · SEO — contenido que trabaja solo

- [ ] Identificar 8-10 keywords con intención real en español
  - "test de ansiedad online", "qué es la sombra jungiana", "test eneagrama gratis"
  - "autoconocimiento psicología", "cómo entender mis patrones de conducta"
- [ ] Un artículo de 1.200-1.500 palabras por keyword
- [ ] Cada artículo termina con CTA al test o Espejo relacionado
- [ ] Frecuencia: un artículo cada 2 semanas
- [ ] Linkear desde Instagram a los artículos cuando se publiquen

---

### 2.E · Contenido — volumen y coherencia

- [ ] Instagram: mantener 3-4 posts semanales de calidad
- [ ] Serie de reels: Franco mostrando una sesión del Espejo con su propio ejemplo
- [ ] Evaluar TikTok con contenido repropuesto de Instagram
- [ ] Newsletter mensual a lista Brevo: reflexión + novedad del producto + próximo programa
- [ ] LinkedIn: caso de estudio mensual desde los practicantes

---

### 2.F · Primer momento híbrido (ads)

**Señal para activar:** Un post orgánico con 3x el engagement promedio del feed.

**Presupuesto inicial:** $100/mes total

- [ ] Boost del post de mayor engagement: $30-50, audiencia similar a seguidores actuales
- [ ] Retargeting visitantes de `app.endonautas.cl` que no se registraron: $30-50
- [ ] No crear creatividad nueva — solo amplificar lo ya probado
- [ ] Medir costo por registro. Benchmark aceptable: menos de $5 por registro

**No activar si:**
- No hay 3 testimonios reales publicados
- El onboarding tiene fricciones sin resolver
- El presupuesto genera estrés financiero

---

## ETAPA 3 — Escala
### Mes 18 al 36 · Objetivo: certificación, ads reales, los 4 flujos activos

---

### 3.A · Producto — estabilidad y diferenciación

- [ ] Exportación de resultados en PDF con branding del terapeuta
- [ ] Espejo v3: sesión compartida practicante-cliente (la IA propone, el terapeuta ajusta)
- [ ] Comunidad dentro de la app — ya hay suficientes usuarios
- [ ] Fondo generativo v3: combina tests + sesiones del Espejo + tiempo de uso

---

### 3.B · Negocio — Formación de Facilitadores

**Estructura:**
- 4-6 módulos: teoría del método + práctica con la plataforma
- Prerequisito: haber completado el Viaje Endonauta
- Modalidad: online asincrónico + 3-4 encuentros en vivo
- Precio: $600-900
- Certificado: "Facilitador Endonauta" — firmado por Franco, respaldado por la plataforma

**Tareas:**
- [ ] Diseñar el currículo completo
- [ ] Plataforma de entrega (puede ser Hotmart o similar)
- [ ] Comunidad privada de facilitadores certificados
- [ ] Meta año 2: 15-20 certificados · Año 3: 30-40 anuales
- [ ] Los certificados tienen acceso perpetuo a actualizaciones del método

---

### 3.C · Ads — el momento real

**Condiciones para escalar ads:**
- LTV promedio conocido
- CAC orgánico de referencia
- Al menos 3 testimonios en video usables como creatividad
- Funnel sin fugas grandes (registro → test → pago)
- $300-500/mes disponibles para quemar aprendiendo

**Secuencia de ads:**

1. **Retargeting (Mes 12-15):** Visitantes que no se registraron · $100/mes · Creatividad: testimonio + prueba gratuita
2. **Lookalike audiences (Mes 15-18):** Similar a compradores del ebook en Hotmart · $200/mes · Creatividad: reel de Franco con sesión real
3. **Frío con lead magnet (Mes 18+):** Test gratuito + interpretación corta como entrada · $300/mes · El ad consigue el registro, la venta viene después

**Principio que guía todo:** No se invierte en ads para crecer. Se invierte para acelerar lo que ya demostró funcionar orgánicamente.

---

## Principios de negocio

1. **Sin inversión externa.** El modelo de certificación y practicantes genera caja real sin diluir nada.
2. **Sin escalar en inglés antes de tener negocio real en español.** La ventaja cultural es local.
3. **Sin ads pagados hasta tener CAC probado.** El dinero en ads sin funnel validado es aprendizaje caro.
4. **El moat no es la tecnología — es la identidad del método.** Lo que protege a Endonautas es la filosofía propia, la comunidad de práctica, y el autor visible. Eso no se copia en 6 meses.
