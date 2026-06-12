# Diagrama de Campañas por Lead Magnet — Flywheel Endonautas
> Versión: 2026-06-02
> Cada lead magnet tiene su propia secuencia de emails.
> Cada email tiene UN CTA que avanza al suscriptor al siguiente paso del flywheel.

---

## 1. LEAD MAGNET: PDF "Descubre tu Máscara" → Lista MÁSCARA

```
Landing /mascara/
  CTA: "Ponle nombre a lo que ya sabes que se repite"
  ↓
Formulario → /suscribir/ (list_slug=mascara)
  ↓
┌──────────────────────────────────────────────────────────────┐
│                  SECUENCIA MÁSCARA (4 emails)                │
├────────┬──────────┬──────────────────────────────────────────┤
│ Email  │ Día      │ Contenido y CTA                         │
├────────┼──────────┼──────────────────────────────────────────┤
│ #1     │ día 0    │ Entrega PDF + cita + aviso spam         │
│        │          │ 🟢 BOTÓN: "Descargar guía de la Máscara"│
│        │          │   → /static/pdfs/descubre-tu-mascara.pdf │
├────────┼──────────┼──────────────────────────────────────────┤
│ #2     │ día 2    │ Profundización: la máscara no es enemiga │
│        │          │ CTA: "Tu herida no es tu identidad"     │
│        │          │ 🟢 BOTÓN APP → Trial MirrorWork          │
│        │          │   Lead: Test Herida (Bourbeau+ECR)       │
├────────┼──────────┼──────────────────────────────────────────┤
│ #3     │ día 4    │ Historia personal de Franco              │
│        │          │ CTA: "No te da respuestas. Preguntas."   │
│        │          │ 🟢 BOTÓN APP → Espejo de Conflictos IA   │
├────────┼──────────┼──────────────────────────────────────────┤
│ #4     │ día 6    │ Invitación app con 3 herramientas        │
│        │          │ CTA: "Tu herida no es tu identidad"      │
│        │          │ 🟢 BOTÓN APP → Registro en MirrorWork    │
└────────┴──────────┴──────────────────────────────────────────┘
  ↓
Trial MirrorWork (100 fractones)
  ↓
Navegante ($10/mes)
```

---

## 2. LEAD MAGNET: PDF "3 Hacks Endonáutica" → Lista HACKS

```
Landing /hacks/
  CTA: "Un hack no es un truco. Es un atajo consciente"
  ↓
Formulario → /suscribir/ (list_slug=hacks)
  ↓
┌──────────────────────────────────────────────────────────────┐
│                  SECUENCIA HACKS (3 emails)                  │
├────────┬──────────┬──────────────────────────────────────────┤
│ Email  │ Día      │ Contenido y CTA                         │
├────────┼──────────┼──────────────────────────────────────────┤
│ #1     │ día 0    │ Entrega PDF + sugerencia de lectura     │
│        │          │ 🟢 BOTÓN: "Descargar guía de los 3 Hacks"│
│        │          │   → /static/pdfs/3-hacks-endonautica.pdf │
├────────┼──────────┼──────────────────────────────────────────┤
│ #2     │ día 3    │ El error de buscar afuera                │
│        │          │ CTA: "Lo que no quieres ver de ti"       │
│        │          │ 🟢 BOTÓN APP → Test Tríada Oscura        │
│        │          │   Lead: Dirty Dozen + Jung + DERS-16     │
├────────┼──────────┼──────────────────────────────────────────┤
│ #3     │ día 6    │ Invitación app                           │
│        │          │ CTA: "Un hack no es un truco"            │
│        │          │ 🟢 BOTÓN APP → Registro en MirrorWork    │
└────────┴──────────┴──────────────────────────────────────────┘
  ↓
Trial MirrorWork (100 fractones)
  ↓
Navegante ($10/mes)
```

---

## 3. LEAD MAGNET: PDF "Guía Viaje Interior" → Lista VIAJE

```
Landing /viaje/
  CTA: "El viaje interior no es un destino. Es una dirección"
  ↓
Formulario → /suscribir/ (list_slug=viaje)
  ↓
┌──────────────────────────────────────────────────────────────┐
│                  SECUENCIA VIAJE (3 emails)                  │
├────────┬──────────┬──────────────────────────────────────────┤
│ Email  │ Día      │ Contenido y CTA                         │
├────────┼──────────┼──────────────────────────────────────────┤
│ #1     │ día 0    │ Entrega PDF + cita + aviso spam         │
│        │          │ 🟢 BOTÓN: "Descargar guía del Viaje"     │
│        │          │   → /static/pdfs/guia-viaje-interior.pdf │
├────────┼──────────┼──────────────────────────────────────────┤
│ #2     │ día 3    │ Por qué la gente da vueltas              │
│        │          │ CTA: "No te da respuestas. Preguntas."   │
│        │          │ 🟢 BOTÓN APP → Espejo de Conflictos IA   │
├────────┼──────────┼──────────────────────────────────────────┤
│ #3     │ día 6    │ Invitación app                           │
│        │          │ CTA: "El viaje interior no es un destino"│
│        │          │ 🟢 BOTÓN APP → Registro en MirrorWork    │
└────────┴──────────┴──────────────────────────────────────────┘
  ↓
Trial MirrorWork (100 fractones)
  ↓
Navegante ($10/mes)
```

---

## Mapa completo del Flywheel

```
                    ┌──────────────────────────────┐
                    │       SEO / INSTAGRAM         │
                    │   (artículos + reels)         │
                    └──────┬───────────┬────────────┘
                           │           │
          ┌────────────────┘           └────────────────┐
          ▼                                              ▼
   PDF LEAD MAGNET                               APP LEAD MAGNET
   (Máscara / Hacks / Viaje)                     (Test / Espejo / Carta)
          │                                              │
          ▼                                              ▼
   EMAIL SEQUENCE                                  TRIAL MIRRORWORK
   (3-4 emails con CTAs progresivos)               (100 fractones)
   Día 0: descarga PDF                                    │
   Día 2-3: profundización + CTA app                     │
   Día 4-6: invitación app                                │
          │                                              │
          └──────────────┬───────────────────────────────┘
                         ▼
                  NAVEGANTE ($10/mes)
                  600 fractones/mes
                  Tests ilimitados + Espejo IA + Mapa Interior
                         │
                         ▼
                  PRACTICANTE ($39/mes)
                  [solo si trabaja con otros]
                  3000 fractones + perfiles de clientes
```

---

## Reglas de CTAs en cada email

| Posición en secuencia | Tipo de CTA | Descripción |
|---|---|---|
| Email 1 (entrega) | 🟢 Descarga PDF | Botón de descarga directa del lead magnet |
| Email 2 (profundización) | 🟢 App | CTA emocional → Trial MirrorWork con test específico |
| Email 3 (conexión) | 🟢 App | CTA emocional → Espejo IA o test complementario |
| Email 4 (invitación, si aplica) | 🟢 App | CTA emocional → Registro en MirrorWork |
