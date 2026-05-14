import json
import os
import threading
from datetime import timedelta

import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import BirthProfile, BirthReport, SIGN_ES, HOUSE_NUM

# ── Human Design constants ─────────────────────────────────────────────────
# Standard Rave Mandala gate sequence (gate 41 at 0° of the wheel).
# The wheel starts at HD_WHEEL_START degrees of tropical longitude.
# Empirically derived from Jovian Archive reference data: gate 41 aligns
# at ~302.5° tropical, meaning the wheel goes clockwise from that point.
HD_WHEEL_START = 302.5

HD_GATES = [
    41,19,13,49,30,55,37,63,22,36,25,17,21,51,42, 3,
    27,24, 2,23, 8,20,16,35,45,12,15,52,39,53,62,56,
    31,33, 7, 4,29,59,40,64,47, 6,46,18,48,57,32,50,
    28,44, 1,43,14,34, 9, 5,26,11,10,58,38,54,61,60,
]

HD_GATE_NAMES = {
    1:'Expresión Creativa',2:'La Dirección',3:'El Orden',4:'Formulación',
    5:'Ritmos Fijos',6:'La Fricción',7:'El Rol del Yo',8:'Contribución',
    9:'Foco',10:'El Amor Propio',11:'Ideas',12:'La Cautela',
    13:'El Escucha',14:'Poder y Habilidades',15:'La Modestia',16:'El Entusiasmo',
    17:'Opiniones',18:'La Corrección',19:'El Querer',20:'El Presente',
    21:'Control',22:'Apertura',23:'Asimilación',24:'La Reflexión',
    25:'La Inocencia',26:'El Egoísta',27:'El Cuidado',28:'El Jugador',
    29:'La Perseverancia',30:'Los Deseos',31:'El Líder',32:'La Continuidad',
    33:'La Retirada',34:'El Poder',35:'El Cambio',36:'La Crisis',
    37:'La Amistad',38:'El Luchador',39:'La Provocación',40:'La Soledad',
    41:'La Contracción',42:'El Crecimiento',43:'La Intuición',44:'La Alerta',
    45:'El Recolector',46:'La Determinación',47:'La Realización',48:'La Profundidad',
    49:'Los Principios',50:'Los Valores',51:'El Choque',52:'La Quietud',
    53:'Los Comienzos',54:'La Ambición',55:'El Espíritu',56:'El Estímulo',
    57:'La Claridad Intuitiva',58:'La Vitalidad',59:'La Sexualidad',60:'La Aceptación',
    61:'La Verdad Interior',62:'Los Detalles',63:'La Duda',64:'La Confusión',
}

HD_PROFILES = {
    (1,1):'1/1 — Investigador/Investigador',
    (1,2):'1/2 — Investigador/Ermitaño',
    (1,3):'1/3 — Investigador/Mártir',
    (1,4):'1/4 — Investigador/Oportunista',
    (2,1):'2/1 — Ermitaño/Investigador',
    (2,2):'2/2 — Ermitaño/Ermitaño',
    (2,3):'2/3 — Ermitaño/Mártir',
    (2,4):'2/4 — Ermitaño/Oportunista',
    (3,1):'3/1 — Mártir/Investigador',
    (3,2):'3/2 — Mártir/Ermitaño',
    (3,3):'3/3 — Mártir/Mártir',
    (3,4):'3/4 — Mártir/Oportunista',
    (4,1):'4/1 — Oportunista/Investigador',
    (4,2):'4/2 — Oportunista/Ermitaño',
    (4,3):'4/3 — Oportunista/Mártir',
    (4,4):'4/4 — Oportunista/Oportunista',
    (5,1):'5/1 — Hereje/Investigador',
    (5,2):'5/2 — Hereje/Ermitaño',
    (5,3):'5/3 — Hereje/Mártir',
    (5,4):'5/4 — Hereje/Oportunista',
    (6,1):'6/1 — Modelo de Rol/Investigador',
    (6,2):'6/2 — Modelo de Rol/Ermitaño',
    (6,3):'6/3 — Modelo de Rol/Mártir',
    (6,4):'6/4 — Modelo de Rol/Oportunista',
}

# Cross type by profile (P☉ line, D☉ line)
_LEFT_ANGLE_PROFILES  = {(5,1),(5,2),(6,2),(6,3)}
_RIGHT_ANGLE_PROFILES = {(1,3),(1,4),(2,4),(2,5),(3,5),(4,6)}
# (4,1) = Juxtaposition; other profiles = Right Angle by default

# Incarnation cross theme names by P☉ gate (Ra Uru Hu convention, Spanish)
HD_CROSS_THEMES = {
     1:'del Amor Propio',        2:'del Retorno',
     3:'de la Mutación',         4:'de la Formulación',
     5:'del Tiempo',             6:'de la Fricción',
     7:'de la Esfinge',          8:'del Contagio',
     9:'del Foco',              10:'del Comportamiento',
    11:'de la Curiosidad',      12:'de la Articulación',
    13:'de la Esfinge',         14:'del Gran Candelabro',
    15:'de las Ondas Cruzadas', 16:'de las Habilidades',
    17:'de las Preguntas',      18:'de la Corrección',
    19:'de la Necesidad',       20:'del Ahora',
    21:'del Control',           22:'de la Gracia',
    23:'de la Asimilación',     24:'de los Cuatro Caminos',
    25:'de la Inocencia',       26:'del Gran Engañador',
    27:'de la Preservación',    28:'del Fatalismo',
    29:'del Compromiso',        30:'del Destino',
    31:'del Liderazgo',         32:'de la Transformación',
    33:'del Retiro',            34:'del Gran Poder',
    35:'del Cambio',            36:'de los Ciclos',
    37:'de los Pactos',         38:'de la Oposición',
    39:'de la Provocación',     40:'de la Abnegación',
    41:'del Deseo',             42:'del Madurar',
    43:'de la Penetración',     44:'de la Alerta',
    45:'del Dominio',           46:'del Descubrimiento',
    47:'de la Realización',     48:'de la Polaridad',
    49:'del Principio',         50:'de los Valores',
    51:'de la Iniciación',      52:'de la Quietud',
    53:'del Comienzo',          54:'de la Ambición',
    55:'de la Abundancia',      56:'del Estímulo',
    57:'de la Claridad',        58:'de la Vitalidad',
    59:'de la Intimidad',       60:'de la Aceptación',
    61:'del Misterio',          62:'de los Detalles',
    63:'de las Preguntas',      64:'de la Confusión',
}

# Centers and their gates
HD_CENTER_GATES = {
    'Cabeza':    [64, 61, 63],
    'Ajna':      [47, 24,  4, 17, 43, 11],
    'Garganta':  [62, 23, 56, 35, 12, 45, 33,  8, 31, 20, 16],
    'Identidad': [13, 25, 46,  2,  1, 15, 10,  7],
    'Corazón':   [21, 40, 26, 51],
    'Plexo Solar':[30, 55, 49, 37, 22, 36,  6],
    'Sacral':    [ 5, 14, 29, 59,  9,  3, 42, 27, 34],
    'Bazo':      [48, 57, 44, 50, 32, 28, 18],
    'Raíz':      [53, 60, 52, 19, 39, 41, 58, 38, 54],
}

# 36 HD channels — (gate_a, gate_b), each gate in a different center
HD_CHANNELS = [
    # Cabeza ↔ Ajna
    (64,47),(61,24),(63,4),
    # Ajna ↔ Garganta
    (17,62),(43,23),(11,56),
    # Garganta ↔ Identidad
    (31,7),(8,1),(33,13),(20,10),
    # Garganta ↔ Sacral / Corazón / Bazo / Plexo Solar
    (20,34),(21,45),(16,48),(12,22),(35,36),
    # Identidad ↔ Sacral / Corazón
    (2,14),(5,15),(29,46),(25,51),
    # Corazón ↔ Bazo / Plexo Solar
    (26,44),(37,40),
    # Plexo Solar ↔ Sacral / Raíz
    (59,6),(19,49),(30,41),(39,55),
    # Sacral ↔ Bazo / Raíz
    (27,50),(34,57),(3,60),(9,52),(42,53),
    # Bazo ↔ Raíz
    (18,58),(28,38),(32,54),
]

# ── Saju constants ─────────────────────────────────────────────────────────
TIANGAN    = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DIZHI      = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
TIAN_ROM   = ['Jiǎ','Yǐ','Bǐng','Dīng','Wù','Jǐ','Gēng','Xīn','Rén','Guǐ']
TIAN_ES    = ['Madera Yang','Madera Yin','Fuego Yang','Fuego Yin','Tierra Yang',
              'Tierra Yin','Metal Yang','Metal Yin','Agua Yang','Agua Yin']
DI_ROM     = ['Zǐ','Chǒu','Yín','Mǎo','Chén','Sì','Wǔ','Wèi','Shēn','Yǒu','Xū','Hài']
DI_ANIMAL  = ['Rata','Buey','Tigre','Conejo','Dragón','Serpiente',
              'Caballo','Cabra','Mono','Gallo','Perro','Cerdo']
DI_ELEM    = ['Agua','Tierra','Madera','Madera','Tierra','Fuego',
              'Fuego','Tierra','Metal','Metal','Tierra','Agua']
ELEMENTS_ES = ['Madera','Fuego','Tierra','Metal','Agua']


def _geocode(place_name):
    try:
        resp = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': place_name, 'format': 'json', 'limit': 1},
            headers={'User-Agent': 'MirrorWork/1.0'},
            timeout=6,
        )
        data = resp.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception:
        pass
    return None, None


def _get_timezone(lat, lng):
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        return tf.timezone_at(lat=lat, lng=lng) or 'UTC'
    except Exception:
        return 'UTC'


def _calculate_astral_chart(bp):
    from kerykeion import AstrologicalSubject

    hour = bp.birth_time.hour if bp.birth_time else 12
    minute = bp.birth_time.minute if bp.birth_time else 0
    lat = bp.latitude or 0.0
    lng = bp.longitude or 0.0
    tz = bp.timezone_str or 'UTC'

    subject = AstrologicalSubject(
        name=str(bp.user.pk),
        year=bp.birth_date.year,
        month=bp.birth_date.month,
        day=bp.birth_date.day,
        hour=hour,
        minute=minute,
        lat=lat,
        lng=lng,
        tz_str=tz,
        zodiac_type='Tropical',
    )

    planet_keys = [
        ('sun', 'Sol'), ('moon', 'Luna'), ('mercury', 'Mercurio'),
        ('venus', 'Venus'), ('mars', 'Marte'), ('jupiter', 'Júpiter'),
        ('saturn', 'Saturno'), ('uranus', 'Urano'), ('neptune', 'Neptuno'),
        ('pluto', 'Plutón'),
    ]

    planets = []
    for attr, label in planet_keys:
        p = getattr(subject, attr)
        sign_es = SIGN_ES.get(p.sign, p.sign)
        planets.append({
            'key': attr,
            'label': label,
            'sign': sign_es,
            'degree': round(float(p.position), 2),
            'house': HOUSE_NUM.get(p.house, 0),
            'retrograde': bool(p.retrograde),
        })

    return {
        'planets': planets,
        'ascendant': {
            'sign': SIGN_ES.get(subject.first_house.sign, subject.first_house.sign),
            'degree': round(float(subject.first_house.position), 2),
        },
        'midheaven': {
            'sign': SIGN_ES.get(subject.tenth_house.sign, subject.tenth_house.sign),
            'degree': round(float(subject.tenth_house.position), 2),
        },
        'birth_time_known': bp.birth_time is not None,
    }


_SYSTEM_ESPEJO = """\
Eres el Espejo Endonauta: un acompañante de autoconocimiento que integra astrología, sistemas de personalidad y filosofía del mundo interior. Tu voz es cálida, directa y poética — no genérica ni clínica.

Marco conceptual que usas:
• Las 12 dimensiones endonautas: Identidad (quién soy en esencia), Sombra (lo rechazado/reprimido), Cuerpo (el cuerpo como mapa), Emociones (el mundo interno), Mente (patrones y creencias), Propósito (dirección y sentido), Espiritualidad (conexión con algo mayor), Vínculos (relaciones e interdependencia), Creatividad (expresión y generatividad), Comunidad (lugar en el mundo), Sueños (inconsciente y visión), Abundancia (relación con recursos y flujo).
• La ley espejo: el mundo exterior refleja el mundo interior; cada configuración natal es una arquitectura de potenciales, no un destino fijo.
• La sombra junguiana: lo que no se integra se proyecta; los planetas retrógrados o en tensión son invitaciones a internalizar.
• El viaje endonauta tiene etapas: despertar, exploración, integración, expresión.

Prohibiciones absolutas:
— No diagnostiques ni pronostiques (no digas "tendrás", "te pasará").
— No seas vago ni genérico: cada lectura debe ser específica a los datos exactos del chart.
— No repitas las palabras clave del chart textualmente sin interpretarlas.
— No uses jerga técnica sin explicar su significado en términos de experiencia interior.
— No hagas listas ni uses títulos de sección. Solo párrafos fluidos.

Idioma: español rioplatense/chileno, informal pero profundo.\
"""


def _kb_context(keywords):
    """Pull 1-2 relevant KB chunks by keyword match for prompt enrichment."""
    try:
        from mirror.models import MirrorChunk
        from django.db.models import Q
        q = Q()
        for kw in keywords:
            q |= Q(contenido__icontains=kw)
        chunks = list(MirrorChunk.objects.filter(q).order_by('?')[:2])
        if chunks:
            return '\n'.join(
                f'[Referencia: {c.documento.nombre}]\n"{c.contenido[:350].strip()}"'
                for c in chunks
            )
    except Exception:
        pass
    return ''


def _build_astral_prompt(chart_data, birth_place):
    planets = chart_data['planets']
    sun  = next(p for p in planets if p['key'] == 'sun')
    moon = next(p for p in planets if p['key'] == 'moon')
    asc  = chart_data['ascendant']
    mc   = chart_data['midheaven']

    retros = [p['label'] for p in planets if p['retrograde']]
    tabla = '\n'.join(
        f"  {p['label']}: {p['sign']} Casa {p['house']}{' ℞' if p['retrograde'] else ''}"
        for p in planets
    )

    # Dominant element from sign distribution
    elem_count = {}
    for p in planets:
        from birth.models import SIGN_ELEMENT
        e = SIGN_ELEMENT.get(p['sign'], '')
        if e:
            elem_count[e] = elem_count.get(e, 0) + 1
    dominant_elem = max(elem_count, key=elem_count.get) if elem_count else ''
    weakest_elem  = min(elem_count, key=elem_count.get) if elem_count else ''

    kb = _kb_context(['sombra', 'proyección', 'arquetipo', 'individuación'])

    prompt = f"""\
CHART COMPLETO — {birth_place}
━━━━━━━━━━━━━━━━━━━━━━━━━
SOL: {sun['sign']} Casa {sun['house']}  |  LUNA: {moon['sign']} Casa {moon['house']}  |  ASC: {asc['sign']}
MC: {mc['sign']}
Retrógrados: {', '.join(retros) if retros else 'ninguno'}
Elemento dominante en el chart: {dominant_elem} | Elemento menos presente: {weakest_elem}

Posiciones completas:
{tabla}
━━━━━━━━━━━━━━━━━━━━━━━━━
{"CONTEXTO DE LA BASE DE CONOCIMIENTOS:" + chr(10) + kb + chr(10) + "━━━━━━━━━━━━━━━━━━━━━━━━━" if kb else ""}

INSTRUCCIÓN DE FORMATO — 5 párrafos en este orden exacto:

1. EL SOL Y LA IDENTIDAD CENTRAL: qué arquetipo de identidad (dimensión Identidad/Propósito) activa el Sol en {sun['sign']} Casa {sun['house']}. Qué brilla naturalmente en esta persona y qué puede costarle admitir de ese mismo brillo.

2. LA LUNA Y EL MUNDO EMOCIONAL: cómo procesa y necesita las emociones (dimensión Emociones/Sombra) con Luna en {moon['sign']} Casa {moon['house']}. Qué patrones emocionales inconscientes puede traer esta posición lunar específica.

3. EL ASCENDENTE Y EL UMBRAL RELACIONAL: cómo se presenta al mundo y qué tipo de experiencias atrae (dimensión Vínculos/Cuerpo) con ASC en {asc['sign']}. La tensión entre la máscara y el interior.

4. EL PATRÓN COMPLETO Y LA SOMBRA DEL CHART: a partir del resto de posiciones y los {len(retros)} planetas retrógrados, qué patrón de sombra o potencial sin desarrollar emerge. Qué elemento o energía el chart pide integrar (dimensión Sombra/Creatividad/Mente).

5. LA INVITACIÓN ACTUAL: sintetizar en qué etapa del viaje endonauta (despertar, exploración, integración, expresión) parece estar esta persona según la configuración del chart, y qué práctica o pregunta interior podría abrir la siguiente etapa.

Termina con UNA pregunta de exploración concreta, no retórica — algo que la persona pueda llevar a su diario o práctica.\
"""
    return prompt


def _deepseek_call(api_key, system_prompt, user_prompt, temperature=0.78, max_tokens=1200):
    resp = requests.post(
        'https://api.deepseek.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json={
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': user_prompt},
            ],
            'temperature': temperature,
            'max_tokens': max_tokens,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']


def _generate_interpretation_async(report_pk, birth_place):
    from django.db import connection
    connection.close()

    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not api_key:
        BirthReport.objects.filter(pk=report_pk).update(status=BirthReport.STATUS_FAILED)
        return

    try:
        report = BirthReport.objects.get(pk=report_pk)
        prompt = _build_astral_prompt(report.chart_data, birth_place)
        text = _deepseek_call(api_key, _SYSTEM_ESPEJO, prompt)
        report.interpretation = text
        report.status = BirthReport.STATUS_COMPLETE
        report.save(update_fields=['interpretation', 'status', 'updated_at'])
    except Exception:
        BirthReport.objects.filter(pk=report_pk).update(status=BirthReport.STATUS_FAILED)


@login_required
def birth_profile(request):
    try:
        bp = request.user.birth_profile
    except BirthProfile.DoesNotExist:
        bp = None

    if request.method == 'POST':
        birth_date = request.POST.get('birth_date', '').strip()
        birth_time = request.POST.get('birth_time', '').strip() or None
        birth_place = request.POST.get('birth_place', '').strip()
        gender = request.POST.get('gender', '').strip()

        if not birth_date or not birth_place:
            return render(request, 'birth/birth_form.html', {
                'bp': bp,
                'error': 'La fecha y el lugar de nacimiento son obligatorios.',
            })

        # Prefer coordinates sent from the autocomplete (already confirmed by user)
        lat_raw = request.POST.get('latitude', '').strip()
        lng_raw = request.POST.get('longitude', '').strip()
        if lat_raw and lng_raw:
            try:
                lat, lng = float(lat_raw), float(lng_raw)
            except ValueError:
                lat, lng = None, None
        else:
            lat, lng = _geocode(birth_place)
        tz_str = _get_timezone(lat, lng) if lat else 'UTC'

        if bp:
            bp.birth_date = birth_date
            bp.birth_time = birth_time
            bp.birth_place = birth_place
            bp.latitude = lat
            bp.longitude = lng
            bp.timezone_str = tz_str
            if gender in ('M', 'F'):
                bp.gender = gender
            bp.save()
        else:
            bp = BirthProfile.objects.create(
                user=request.user,
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=birth_place,
                latitude=lat,
                longitude=lng,
                timezone_str=tz_str,
                gender=gender if gender in ('M', 'F') else '',
            )

        return redirect('birth:profile')

    reports = {}
    if bp:
        for rtype in [BirthReport.TYPE_ASTRAL, BirthReport.TYPE_HD, BirthReport.TYPE_SAJU]:
            reports[rtype] = BirthReport.objects.filter(
                user=request.user, report_type=rtype
            ).first()

    return render(request, 'birth/birth_form.html', {
        'bp': bp,
        'astral_report': reports.get(BirthReport.TYPE_ASTRAL),
        'hd_report':     reports.get(BirthReport.TYPE_HD),
        'saju_report':   reports.get(BirthReport.TYPE_SAJU),
    })


@login_required
def astral_generate(request):
    if request.method != 'POST':
        return redirect('birth:profile')

    try:
        bp = request.user.birth_profile
    except BirthProfile.DoesNotExist:
        return redirect('birth:profile')

    chart_data = _calculate_astral_chart(bp)

    report, _ = BirthReport.objects.update_or_create(
        user=request.user,
        report_type=BirthReport.TYPE_ASTRAL,
        defaults={
            'chart_data': chart_data,
            'status': BirthReport.STATUS_COMPLETE,
            'interpretation': '',
        },
    )
    return redirect('birth:astral_detail', pk=report.pk)


@login_required
def astral_detail(request, pk):
    report = get_object_or_404(
        BirthReport, pk=pk, user=request.user, report_type=BirthReport.TYPE_ASTRAL
    )
    try:
        bp = request.user.birth_profile
    except BirthProfile.DoesNotExist:
        bp = None

    return render(request, 'birth/astral_detail.html', {
        'report': report,
        'bp': bp,
        'poll_url': f'/nacimiento/reporte/{report.pk}/estado/',
        'is_processing': report.status == BirthReport.STATUS_PROCESSING,
    })


@login_required
def report_status(request, pk):
    report = get_object_or_404(BirthReport, pk=pk, user=request.user)
    return JsonResponse({
        'status': report.status,
        'interpretation': report.interpretation if report.status == BirthReport.STATUS_COMPLETE else '',
    })


# ── Human Design ───────────────────────────────────────────────────────────

def _lon_to_gate_line(lon):
    gate_size = 360.0 / 64
    wheel_pos = (lon - HD_WHEEL_START + 360) % 360
    idx = int(wheel_pos / gate_size) % 64
    gate = HD_GATES[idx]
    line = int((wheel_pos % gate_size) / (gate_size / 6)) + 1
    return gate, min(line, 6)


def _calculate_hd_chart(bp):
    from kerykeion import AstrologicalSubject
    import pytz
    from datetime import datetime as _dt
    from collections import deque

    hour = bp.birth_time.hour if bp.birth_time else 12
    minute = bp.birth_time.minute if bp.birth_time else 0
    lat = bp.latitude or 0.0
    lng = bp.longitude or 0.0
    tz = bp.timezone_str or 'UTC'

    # Convert birth time to UTC for accurate astronomical calculation
    tz_obj = pytz.timezone(tz)
    birth_naive = _dt(bp.birth_date.year, bp.birth_date.month, bp.birth_date.day, hour, minute)
    birth_aware = tz_obj.localize(birth_naive)
    birth_utc = birth_aware.astimezone(pytz.UTC)

    # Personality chart (birth moment in UTC)
    p = AstrologicalSubject('p',
        birth_utc.year, birth_utc.month, birth_utc.day,
        birth_utc.hour, birth_utc.minute,
        lat=lat, lng=lng, tz_str='UTC', zodiac_type='Tropical')

    # Design chart: exactly 88 days before birth (UTC)
    design_utc = birth_utc - timedelta(days=88)
    d = AstrologicalSubject('d',
        design_utc.year, design_utc.month, design_utc.day,
        design_utc.hour, design_utc.minute,
        lat=lat, lng=lng, tz_str='UTC', zodiac_type='Tropical')

    def gl(lon):
        return _lon_to_gate_line(lon)

    def make_planet(label, symbol, lon):
        g, l = gl(lon)
        return {'label': label, 'symbol': symbol, 'gate': g, 'line': l, 'name': HD_GATE_NAMES.get(g, '')}

    # Earth is always opposite the Sun (180°)
    personality_planets = [
        make_planet('Sol',         '⊙', p.sun.abs_pos),
        make_planet('Tierra',      '⊕', (p.sun.abs_pos + 180) % 360),
        make_planet('Luna',        '☽', p.moon.abs_pos),
        make_planet('Nodo Norte',  '☊', p.true_north_lunar_node.abs_pos),
        make_planet('Nodo Sur',    '☋', p.true_south_lunar_node.abs_pos),
        make_planet('Mercurio',    '☿', p.mercury.abs_pos),
        make_planet('Venus',       '♀', p.venus.abs_pos),
        make_planet('Marte',       '♂', p.mars.abs_pos),
        make_planet('Júpiter',     '♃', p.jupiter.abs_pos),
        make_planet('Saturno',     '♄', p.saturn.abs_pos),
        make_planet('Urano',       '♅', p.uranus.abs_pos),
        make_planet('Neptuno',     '♆', p.neptune.abs_pos),
        make_planet('Plutón',      '♇', p.pluto.abs_pos),
    ]

    design_planets = [
        make_planet('Sol',         '⊙', d.sun.abs_pos),
        make_planet('Tierra',      '⊕', (d.sun.abs_pos + 180) % 360),
        make_planet('Luna',        '☽', d.moon.abs_pos),
        make_planet('Nodo Norte',  '☊', d.true_north_lunar_node.abs_pos),
        make_planet('Nodo Sur',    '☋', d.true_south_lunar_node.abs_pos),
        make_planet('Mercurio',    '☿', d.mercury.abs_pos),
        make_planet('Venus',       '♀', d.venus.abs_pos),
        make_planet('Marte',       '♂', d.mars.abs_pos),
        make_planet('Júpiter',     '♃', d.jupiter.abs_pos),
        make_planet('Saturno',     '♄', d.saturn.abs_pos),
        make_planet('Urano',       '♅', d.uranus.abs_pos),
        make_planet('Neptuno',     '♆', d.neptune.abs_pos),
        make_planet('Plutón',      '♇', d.pluto.abs_pos),
    ]

    p_sun_g, p_sun_l   = personality_planets[0]['gate'], personality_planets[0]['line']
    p_earth_g, p_earth_l = personality_planets[1]['gate'], personality_planets[1]['line']
    d_sun_g, d_sun_l   = design_planets[0]['gate'], design_planets[0]['line']
    d_earth_g, d_earth_l = design_planets[1]['gate'], design_planets[1]['line']

    # All active gates from both charts
    active_gates = set()
    for pl in personality_planets + design_planets:
        active_gates.add(pl['gate'])

    # Gate-to-center lookup
    gate_to_center = {}
    for center, gates in HD_CENTER_GATES.items():
        for g in gates:
            gate_to_center[g] = center

    # Centers defined ONLY through complete channels (both gates active)
    defined_centers = set()
    for ch in HD_CHANNELS:
        g_a, g_b = ch
        if g_a in active_gates and g_b in active_gates:
            ctr_a = gate_to_center.get(g_a)
            ctr_b = gate_to_center.get(g_b)
            if ctr_a:
                defined_centers.add(ctr_a)
            if ctr_b:
                defined_centers.add(ctr_b)

    # Center adjacency from defined channels (both gates must be active)
    center_adj = {}
    defined_channels = []
    for ch in HD_CHANNELS:
        g_a, g_b = ch
        if g_a in active_gates and g_b in active_gates:
            ctr_a = gate_to_center.get(g_a)
            ctr_b = gate_to_center.get(g_b)
            if ctr_a and ctr_b and ctr_a != ctr_b:
                center_adj.setdefault(ctr_a, set()).add(ctr_b)
                center_adj.setdefault(ctr_b, set()).add(ctr_a)
                defined_channels.append({
                    'gates': f'{g_a}–{g_b}',
                    'name': f'{HD_GATE_NAMES.get(g_a, "")} / {HD_GATE_NAMES.get(g_b, "")}',
                })

    # BFS from Garganta to find reachable centers via defined channels
    reachable_from_throat = set()
    if 'Garganta' in center_adj:
        queue = deque(['Garganta'])
        visited = {'Garganta'}
        while queue:
            c = queue.popleft()
            for neighbor in center_adj.get(c, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    reachable_from_throat.add(neighbor)
                    queue.append(neighbor)

    sacral_defined = 'Sacral' in defined_centers
    motor_centers = {'Corazón', 'Plexo Solar', 'Raíz', 'Sacral'}
    motors_from_throat = reachable_from_throat & motor_centers

    if sacral_defined and motors_from_throat:
        hd_type = 'Generador Manifestante'
        strategy = 'Responder y luego informar antes de actuar'
        not_self = 'Frustración / Ira'
        signature = 'Paz y satisfacción'
    elif sacral_defined:
        hd_type = 'Generador'
        strategy = 'Responder (esperar una señal del entorno)'
        not_self = 'Frustración'
        signature = 'Satisfacción'
    elif motors_from_throat:
        hd_type = 'Manifestador'
        strategy = 'Informar antes de actuar'
        not_self = 'Ira'
        signature = 'Paz'
    elif defined_centers:
        hd_type = 'Proyector'
        strategy = 'Esperar la invitación'
        not_self = 'Amargura'
        signature = 'Éxito'
    else:
        hd_type = 'Reflector'
        strategy = 'Esperar un ciclo lunar completo (29 días)'
        not_self = 'Decepción'
        signature = 'Sorpresa'

    # Profile = Personality Sun line + Design Sun line
    profile = HD_PROFILES.get((p_sun_l, d_sun_l), f'{p_sun_l}/{d_sun_l}')

    # Authority (center hierarchy)
    if 'Plexo Solar' in defined_centers:
        authority = 'Emocional — Plexo Solar'
    elif 'Sacral' in defined_centers:
        authority = 'Sacral'
    elif 'Bazo' in defined_centers:
        authority = 'Esplénico — Bazo'
    elif 'Corazón' in defined_centers:
        authority = 'Ego — Corazón'
    elif 'Identidad' in defined_centers:
        authority = 'Identidad — G'
    elif hd_type == 'Reflector':
        authority = 'Lunar — 29 días'
    else:
        authority = 'Mental — Externo'

    # Definition: count connected components among defined centers
    visited_def = set()
    components = 0
    for center in defined_centers:
        if center not in visited_def:
            components += 1
            q = deque([center])
            visited_def.add(center)
            while q:
                c = q.popleft()
                for neighbor in center_adj.get(c, []):
                    if neighbor in defined_centers and neighbor not in visited_def:
                        visited_def.add(neighbor)
                        q.append(neighbor)
    if components == 0:
        definition = 'Indefinido'
    elif components == 1:
        definition = 'Definición Simple'
    elif components == 2:
        definition = 'Definición Partida'
    elif components == 3:
        definition = 'Definición Partida Triple'
    else:
        definition = 'Definición Cuádruple'

    planets_paired = [
        {'p': pp, 'd': dp}
        for pp, dp in zip(personality_planets, design_planets)
    ]

    cross_gate_info = [
        {'gate': p_sun_g,   'name': HD_GATE_NAMES.get(p_sun_g, ''),   'role': 'P ☉'},
        {'gate': p_earth_g, 'name': HD_GATE_NAMES.get(p_earth_g, ''), 'role': 'P ⊕'},
        {'gate': d_sun_g,   'name': HD_GATE_NAMES.get(d_sun_g, ''),   'role': 'D ☉'},
        {'gate': d_earth_g, 'name': HD_GATE_NAMES.get(d_earth_g, ''), 'role': 'D ⊕'},
    ]

    # Named incarnation cross
    _profile_key = (p_sun_l, d_sun_l)
    if _profile_key == (4, 1):
        _cross_type = 'Yuxtaposición'
    elif _profile_key in _LEFT_ANGLE_PROFILES:
        _cross_type = 'Ángulo Izquierdo'
    else:
        _cross_type = 'Ángulo Derecho'
    _theme = HD_CROSS_THEMES.get(p_sun_g, '')
    _gate_notation = f'({p_sun_g}/{p_earth_g} | {d_sun_g}/{d_earth_g})'
    cross_name = f'Cruz de {_cross_type} {_theme} {_gate_notation}'.strip()

    return {
        'type':             hd_type,
        'strategy':         strategy,
        'not_self_theme':   not_self,
        'signature':        signature,
        'profile':          profile,
        'authority':        authority,
        'definition':       definition,
        'defined_centers':  sorted(defined_centers),
        'active_gates':     sorted(active_gates),
        'defined_channels': defined_channels,
        'cross_gates':      cross_gate_info,
        'cross_str':        f'{p_sun_g}/{p_earth_g} | {d_sun_g}/{d_earth_g}',
        'cross_name':       cross_name,
        'design_date':      design_utc.strftime('%Y-%m-%d'),
        'planets_paired':   planets_paired,
        'personality': {
            'sun':   {'gate': p_sun_g,   'line': p_sun_l,   'name': HD_GATE_NAMES.get(p_sun_g, '')},
            'earth': {'gate': p_earth_g, 'line': p_earth_l, 'name': HD_GATE_NAMES.get(p_earth_g, '')},
        },
        'design': {
            'sun':   {'gate': d_sun_g,   'line': d_sun_l,   'name': HD_GATE_NAMES.get(d_sun_g, '')},
            'earth': {'gate': d_earth_g, 'line': d_earth_l, 'name': HD_GATE_NAMES.get(d_earth_g, '')},
        },
    }


def _build_hd_prompt(chart_data, birth_place):
    p = chart_data['personality']
    d = chart_data['design']
    channels_str = ', '.join(
        f"{ch['gates']} ({ch['name']})"
        for ch in chart_data.get('defined_channels', [])
    ) or 'ninguno definido'
    centers_str = ', '.join(chart_data['defined_centers'])
    undefined = [c for c in ['Cabeza','Ajna','Garganta','Identidad','Corazón',
                              'Plexo Solar','Sacral','Bazo','Raíz']
                 if c not in chart_data['defined_centers']]

    kb = _kb_context(['autorregulación', 'observador', 'toma de decisiones', 'cuerpo energético'])

    prompt = f"""\
DISEÑO HUMANO — {birth_place}
━━━━━━━━━━━━━━━━━━━━━━━━━
TIPO: {chart_data['type']}
ESTRATEGIA: {chart_data['strategy']}
AUTORIDAD: {chart_data.get('authority','')}
PERFIL: {chart_data['profile']}
DEFINICIÓN: {chart_data.get('definition','')}
TEMA NO-YO / FIRMA: {chart_data['not_self_theme']} → {chart_data.get('signature','')}

PUERTAS DEL SOL (consciente ↔ inconsciente):
  Personalidad Sol: Puerta {p['sun']['gate']} — {p['sun']['name']} (Línea {p['sun']['line']})
  Personalidad Tierra: Puerta {p['earth']['gate']} — {p['earth']['name']} (Línea {p['earth']['line']})
  Diseño Sol: Puerta {d['sun']['gate']} — {d['sun']['name']} (Línea {d['sun']['line']})
  Diseño Tierra: Puerta {d['earth']['gate']} — {d['earth']['name']} (Línea {d['earth']['line']})

CENTROS DEFINIDOS ({len(chart_data['defined_centers'])}): {centers_str}
CENTROS ABIERTOS ({len(undefined)}): {', '.join(undefined) if undefined else 'ninguno'}
CANALES DEFINIDOS: {channels_str}
━━━━━━━━━━━━━━━━━━━━━━━━━
{"CONTEXTO DE LA BASE DE CONOCIMIENTOS:" + chr(10) + kb + chr(10) + "━━━━━━━━━━━━━━━━━━━━━━━━━" if kb else ""}

INSTRUCCIÓN DE FORMATO — 5 párrafos en este orden exacto:

1. TIPO Y ESTRATEGIA EN LA VIDA COTIDIANA: no describas el tipo en abstracto — muestra cómo se manifiesta concretamente ser un {chart_data['type']} con estrategia "{chart_data['strategy']}" en el día a día, en el trabajo, en las relaciones. Qué fricción genera ignorar esta estrategia (dimensión Identidad/Cuerpo).

2. AUTORIDAD INTERIOR — LA FORMA DE DECIDIR: explica cómo esta persona toma decisiones alineadas con su diseño usando su autoridad {chart_data.get('authority','')}. Sé específico sobre el proceso interno (esperar, sentir, saber): no la definas en abstracto, muéstrala en una situación concreta (dimensión Emociones/Mente).

3. EL PERFIL Y EL ROL DE VIDA: el perfil {chart_data['profile']} define el patrón de cómo esta persona aprende y contribuye. Describe qué tipo de experiencias tiende a atraer, qué conflicto interno genera el perfil y cuál es el don que emerge cuando lo vive conscientemente (dimensión Propósito/Vínculos).

4. LAS PUERTAS DEL SOL — EL HILO CONSCIENTE E INCONSCIENTE: la Puerta {p['sun']['gate']} ({p['sun']['name']}) es la energía que esta persona irradia conscientemente; la Puerta {d['sun']['gate']} ({d['sun']['name']}) opera desde el inconsciente como una corriente de fondo. Cómo se integran o se tensionan (dimensión Creatividad/Sombra/Espiritualidad).

5. CENTROS DEFINIDOS, CENTROS ABIERTOS Y EL TEMA NO-YO: los centros definidos ({centers_str}) son energías consistentes que esta persona tiene para dar. Los centros abiertos son donde más fácilmente absorbe y se condiciona. Cómo se manifiesta el tema No-Yo "{chart_data['not_self_theme']}" y cómo reconocer cuando uno está viviendo desde el diseño vs. el condicionamiento (dimensión Sombra/Abundancia/Comunidad).

Termina con UNA pregunta de exploración concreta — algo que apunte directamente a la tensión más viva que surge de este diseño específico.\
"""
    return prompt


def _generate_hd_async(report_pk, birth_place):
    from django.db import connection
    connection.close()
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not api_key:
        BirthReport.objects.filter(pk=report_pk).update(status=BirthReport.STATUS_FAILED)
        return
    try:
        report = BirthReport.objects.get(pk=report_pk)
        prompt = _build_hd_prompt(report.chart_data, birth_place)
        text = _deepseek_call(api_key, _SYSTEM_ESPEJO, prompt)
        report.interpretation = text
        report.status = BirthReport.STATUS_COMPLETE
        report.save(update_fields=['interpretation', 'status', 'updated_at'])
    except Exception:
        BirthReport.objects.filter(pk=report_pk).update(status=BirthReport.STATUS_FAILED)


@login_required
def hd_generate(request):
    if request.method != 'POST':
        return redirect('birth:profile')
    try:
        bp = request.user.birth_profile
    except BirthProfile.DoesNotExist:
        return redirect('birth:profile')

    chart_data = _calculate_hd_chart(bp)
    report, _ = BirthReport.objects.update_or_create(
        user=request.user, report_type=BirthReport.TYPE_HD,
        defaults={'chart_data': chart_data, 'status': BirthReport.STATUS_COMPLETE, 'interpretation': ''},
    )
    return redirect('birth:hd_detail', pk=report.pk)


@login_required
def hd_detail(request, pk):
    report = get_object_or_404(BirthReport, pk=pk, user=request.user, report_type=BirthReport.TYPE_HD)
    try:
        bp = request.user.birth_profile
    except BirthProfile.DoesNotExist:
        bp = None
    return render(request, 'birth/hd_detail.html', {
        'report': report, 'bp': bp,
        'poll_url': f'/nacimiento/reporte/{report.pk}/estado/',
    })


# ── Saju ───────────────────────────────────────────────────────────────────

def _true_solar_hour_minute(bp):
    """Return (h, m, correction_minutes_int) adjusted for true solar time, or (None, None, 0)."""
    if not bp.birth_time or bp.longitude is None or not bp.timezone_str:
        return None, None, 0
    try:
        import pytz
        from datetime import datetime as _dt, timedelta as _td
        tz = pytz.timezone(bp.timezone_str)
        naive = _dt(bp.birth_date.year, bp.birth_date.month, bp.birth_date.day,
                    bp.birth_time.hour, bp.birth_time.minute)
        aware = tz.localize(naive)
        utc_offset_h = aware.utcoffset().total_seconds() / 3600
        std_meridian = utc_offset_h * 15
        correction = (bp.longitude - std_meridian) * 4  # minutes
        corrected = naive + _td(minutes=correction)
        return corrected.hour, corrected.minute, round(correction)
    except Exception:
        return bp.birth_time.hour, bp.birth_time.minute, 0


def _calculate_daewoon(bp, mo_tg, mo_dz, yr_tg):
    """Calculate 大運 10-year luck cycles using sxtwl month-GZ transitions as 節 markers."""
    import sxtwl
    from datetime import timedelta

    gender = getattr(bp, 'gender', '') or ''
    if not gender:
        return None

    # Yang stems: 甲(0) 丙(2) 戊(4) 庚(6) 壬(8) — even indices
    is_yang_year = (yr_tg % 2 == 0)
    is_male = (gender == 'M')
    # 顺运 when year polarity matches gender polarity
    forward = (is_yang_year == is_male)

    birth_date = bp.birth_date
    birth_d = sxtwl.fromSolar(birth_date.year, birth_date.month, birth_date.day)
    birth_mo_tg = birth_d.getMonthGZ().tg
    birth_mo_dz = birth_d.getMonthGZ().dz

    # Find nearest 節 by detecting day when month GZ transitions
    if not forward:
        # Count back to previous 節 (last time month GZ changed)
        for i in range(1, 45):
            check = birth_date - timedelta(days=i)
            chk_mo = sxtwl.fromSolar(check.year, check.month, check.day).getMonthGZ()
            if chk_mo.tg != birth_mo_tg or chk_mo.dz != birth_mo_dz:
                jie_date = check + timedelta(days=1)
                days_diff = (birth_date - jie_date).days
                break
        else:
            return None
    else:
        # Count forward to next 節
        for i in range(1, 45):
            check = birth_date + timedelta(days=i)
            chk_mo = sxtwl.fromSolar(check.year, check.month, check.day).getMonthGZ()
            if chk_mo.tg != birth_mo_tg or chk_mo.dz != birth_mo_dz:
                jie_date = check
                days_diff = (jie_date - birth_date).days
                break
        else:
            return None

    start_age = round(days_diff / 3)
    step = 1 if forward else -1
    import datetime
    current_age = datetime.date.today().year - birth_date.year

    cycles = []
    tg, dz = mo_tg, mo_dz
    for i in range(9):
        tg = (tg + step) % 10
        dz = (dz + step) % 12
        age_start = start_age + i * 10
        age_end   = age_start + 9
        cycles.append({
            'stem':        TIANGAN[tg],
            'branch':      DIZHI[dz],
            'rom_stem':    TIAN_ROM[tg],
            'rom_branch':  DI_ROM[dz],
            'elem_stem':   TIAN_ES[tg],
            'elem_branch': DI_ELEM[dz],
            'animal':      DI_ANIMAL[dz],
            'age_start':   age_start,
            'age_end':     age_end,
            'year_start':  birth_date.year + age_start,
            'year_end':    birth_date.year + age_end,
            'is_current':  age_start <= current_age <= age_end,
        })

    current_cycle = next((c for c in cycles if c['is_current']), None)
    return {
        'cycles':        cycles,
        'start_age':     start_age,
        'direction':     'forward' if forward else 'backward',
        'current_cycle': current_cycle,
    }


def _calculate_saju_chart(bp):
    import sxtwl

    d = sxtwl.fromSolar(bp.birth_date.year, bp.birth_date.month, bp.birth_date.day)
    yr = d.getYearGZ(True)
    mo = d.getMonthGZ()
    dy = d.getDayGZ()

    # True solar time correction for the hour pillar
    solar_h, solar_m, correction_min = _true_solar_hour_minute(bp)
    if solar_h is not None:
        hour = solar_h
    elif bp.birth_time:
        hour = bp.birth_time.hour
    else:
        hour = None

    hr_gz = sxtwl.getShiGz(dy.tg, hour if hour is not None else 12)

    def gz_info(gz, label):
        elem_full = TIAN_ES[gz.tg]          # e.g. 'Metal Yang'
        elem_name = elem_full.split()[0]     # e.g. 'Metal'
        return {
            'label':          label,
            'stem':           TIANGAN[gz.tg],
            'branch':         DIZHI[gz.dz],
            'rom_stem':       TIAN_ROM[gz.tg],
            'rom_branch':     DI_ROM[gz.dz],
            'elem_stem':      elem_full,
            'elem_stem_name': elem_name,     # for CSS class
            'animal':         DI_ANIMAL[gz.dz],
            'elem_branch':    DI_ELEM[gz.dz],
        }

    pillars = [
        gz_info(yr, 'Año'),
        gz_info(mo, 'Mes'),
        gz_info(dy, 'Día'),
        gz_info(hr_gz, 'Hora'),
    ]

    # Element count — always all 5 elements, including zeros
    full_count = {e: 0 for e in ELEMENTS_ES}
    for p in pillars:
        full_count[p['elem_stem_name']] += 1
        full_count[p['elem_branch']]    += 1

    dominant = max(full_count, key=full_count.get)
    min_val  = min(full_count.values())
    weakest_list = [e for e, c in full_count.items() if c == min_val]
    weakest = ' / '.join(weakest_list) if min_val < max(full_count.values()) else None

    daewoon = _calculate_daewoon(bp, mo.tg, mo.dz, yr.tg)

    return {
        'pillars':            pillars,
        'element_count':      full_count,
        'dominant_element':   dominant,
        'weakest_element':    weakest,
        'day_master':         TIAN_ES[dy.tg],
        'hour_known':         bp.birth_time is not None,
        'lunar_year_animal':  DI_ANIMAL[yr.dz],
        'solar_correction_min': correction_min,
        'solar_hour':         solar_h,
        'solar_minute':       solar_m,
        'daewoon':            daewoon,
    }


def _build_saju_prompt(chart_data, birth_place):
    pillars = chart_data['pillars']
    ec = chart_data['element_count']
    daewoon = chart_data.get('daewoon')

    p_lines = '\n'.join(
        f"  Pilar {p['label']}: {p['stem']} ({p['rom_stem']}) — {p['elem_stem']} | "
        f"Rama {p['branch']} ({p['rom_branch']}) — {p['elem_branch']}, {p['animal']}"
        for p in pillars
    )
    elem_line = '  ' + ' | '.join(f"{e}: {ec.get(e,0)}" for e in ELEMENTS_ES)

    current = None
    next_cycle = None
    if daewoon:
        current = daewoon.get('current_cycle')
        if current:
            idx = daewoon['cycles'].index(current)
            next_cycle = daewoon['cycles'][idx+1] if idx < len(daewoon['cycles'])-1 else None

    daewoon_block = ''
    if current:
        daewoon_block = (
            f"\nCICLO VITAL ACTUAL (大運):\n"
            f"  {current['stem']}{current['branch']} — {current['elem_stem']} sobre {current['elem_branch']}\n"
            f"  Período: edades {current['age_start']}–{current['age_end']} "
            f"({current['year_start']}–{current['year_end']})\n"
        )
        if next_cycle:
            daewoon_block += (
                f"Próximo ciclo (comienza ~{next_cycle['year_start']}): "
                f"{next_cycle['stem']}{next_cycle['branch']} — {next_cycle['elem_stem']}\n"
            )

    kb = _kb_context(['cinco elementos', 'yin yang', 'fluir', 'Qi', 'madera fuego tierra metal agua'])

    # Day master decomposed: e.g. "Madera Yang" → element=Madera, polarity=Yang
    day_master_parts = chart_data['day_master'].split()
    dm_elem = day_master_parts[0] if day_master_parts else chart_data['day_master']
    dm_pol  = day_master_parts[1] if len(day_master_parts) > 1 else ''

    prompt = f"""\
SAJU — CUATRO PILARES DEL DESTINO — {birth_place}
━━━━━━━━━━━━━━━━━━━━━━━━━
MAESTRO DEL DÍA: {chart_data['day_master']} (elemento {dm_elem}, polaridad {dm_pol})
ANIMAL DEL AÑO: {chart_data['lunar_year_animal']}

CUATRO PILARES (四柱八字):
{p_lines}

BALANCE ELEMENTAL (8 caracteres totales):
{elem_line}
  Dominante: {chart_data['dominant_element']} | Mínimo/ausente: {chart_data.get('weakest_element','equilibrado')}
{daewoon_block}━━━━━━━━━━━━━━━━━━━━━━━━━
{"CONTEXTO DE LA BASE DE CONOCIMIENTOS:" + chr(10) + kb + chr(10) + "━━━━━━━━━━━━━━━━━━━━━━━━━" if kb else ""}

INSTRUCCIÓN DE FORMATO — 5 párrafos en este orden exacto:

1. EL MAESTRO DEL DÍA — LA NATURALEZA CENTRAL: el Maestro del Día {chart_data['day_master']} define la energía esencial. No describas el elemento en abstracto — explica cómo se manifiesta como carácter, como forma de relacionarse con el mundo, qué tipo de fuerza interna tiene y dónde esa misma fuerza puede convertirse en rigidez o herida (dimensión Identidad/Cuerpo). Usa el elemento {dm_elem} como metáfora viva.

2. EL BALANCE ELEMENTAL — LO QUE SOBRA Y LO QUE FALTA: con {chart_data['dominant_element']} como elemento dominante y {chart_data.get('weakest_element','equilibrio') or 'equilibrio'} como el menos presente, describe qué tipo de energía gobierna la vida de esta persona y qué área de vida (emoción, relación, acción, reflexión, flujo) tiende a estar subdesarrollada. Qué prácticas o arquetipos podrían cultivar el elemento faltante (dimensión Emociones/Abundancia/Cuerpo).

3. EL ANIMAL DEL AÑO Y LOS PATRONES RELACIONALES: el {chart_data['lunar_year_animal']} como arquetipo relacional — cómo esta persona se mueve en sus vínculos, qué tipo de dinámicas tiende a atraer y qué patrón inconsciente en las relaciones refleja el animal (dimensión Vínculos/Sombra).

4. LAS TENSIONES INTERNAS — EL PATRÓN QUE SE REPITE: leyendo los pilares de Mes, Día y Hora juntos (los tres pilares más personales), qué tensión o fricción elemental existe entre ellos. Qué conflicto interno se repite, qué patrón inconsciente emerge de esa configuración específica y cómo se manifiesta en decisiones o bloqueos recurrentes (dimensión Mente/Sombra/Creatividad).

5. EL CICLO VITAL ACTUAL — EL CAPÍTULO PRESENTE: {"con el ciclo actual de " + current['elem_stem'] + " sobre " + current['elem_branch'] + " (edades " + str(current['age_start']) + "–" + str(current['age_end']) + "), qué tipo de energía y aprendizaje está disponible en este período. Qué está pidiendo ser soltado y qué está emergiendo. Cómo prepararse para el próximo ciclo" + (" de " + next_cycle['elem_stem'] if next_cycle else "") + " (dimensión Propósito/Espiritualidad/Sueños)." if current else "describirás los ciclos vitales generales según los pilares disponibles, ya que no se cuenta con el ciclo 大運 actual."}

Termina con UNA pregunta de exploración concreta — algo específico a esta carta, no una pregunta genérica sobre crecimiento personal.\
"""
    return prompt


def _generate_saju_async(report_pk, birth_place):
    from django.db import connection
    connection.close()
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not api_key:
        BirthReport.objects.filter(pk=report_pk).update(status=BirthReport.STATUS_FAILED)
        return
    try:
        report = BirthReport.objects.get(pk=report_pk)
        prompt = _build_saju_prompt(report.chart_data, birth_place)
        text = _deepseek_call(api_key, _SYSTEM_ESPEJO, prompt)
        report.interpretation = text
        report.status = BirthReport.STATUS_COMPLETE
        report.save(update_fields=['interpretation', 'status', 'updated_at'])
    except Exception:
        BirthReport.objects.filter(pk=report_pk).update(status=BirthReport.STATUS_FAILED)


@login_required
def saju_generate(request):
    if request.method != 'POST':
        return redirect('birth:profile')
    try:
        bp = request.user.birth_profile
    except BirthProfile.DoesNotExist:
        return redirect('birth:profile')

    chart_data = _calculate_saju_chart(bp)
    report, _ = BirthReport.objects.update_or_create(
        user=request.user, report_type=BirthReport.TYPE_SAJU,
        defaults={'chart_data': chart_data, 'status': BirthReport.STATUS_COMPLETE, 'interpretation': ''},
    )
    return redirect('birth:saju_detail', pk=report.pk)


@login_required
def saju_detail(request, pk):
    report = get_object_or_404(BirthReport, pk=pk, user=request.user, report_type=BirthReport.TYPE_SAJU)
    try:
        bp = request.user.birth_profile
    except BirthProfile.DoesNotExist:
        bp = None
    return render(request, 'birth/saju_detail.html', {
        'report': report, 'bp': bp,
        'poll_url': f'/nacimiento/reporte/{report.pk}/estado/',
    })


# ── Lectura endonauta (vistas de interpretación AI) ───────────────────────

_BIRTH_TYPE_LABELS = {
    BirthReport.TYPE_ASTRAL: 'Carta Astral',
    BirthReport.TYPE_HD:     'Diseño Humano',
    BirthReport.TYPE_SAJU:   'Saju',
}

_BIRTH_ASYNC_FNS = {
    BirthReport.TYPE_ASTRAL: _generate_interpretation_async,
    BirthReport.TYPE_HD:     _generate_hd_async,
    BirthReport.TYPE_SAJU:   _generate_saju_async,
}

_BIRTH_LECTURA_NAMES = {
    BirthReport.TYPE_ASTRAL: 'astral_lectura',
    BirthReport.TYPE_HD:     'hd_lectura',
    BirthReport.TYPE_SAJU:   'saju_lectura',
}


def _birth_lectura_view(request, pk, report_type):
    from django.urls import reverse
    report = get_object_or_404(BirthReport, pk=pk, user=request.user, report_type=report_type)
    is_processing = report.interpretation == 'processing'
    is_revealed   = bool(report.interpretation) and report.interpretation != 'processing'
    _detail_names = {
        BirthReport.TYPE_ASTRAL: 'birth:astral_detail',
        BirthReport.TYPE_HD:     'birth:hd_detail',
        BirthReport.TYPE_SAJU:   'birth:saju_detail',
    }
    back_view = _detail_names.get(report_type, 'birth:profile')
    return render(request, 'birth/lectura.html', {
        'report':        report,
        'label':         _BIRTH_TYPE_LABELS.get(report_type, ''),
        'is_processing': is_processing,
        'is_revealed':   is_revealed,
        'poll_url':      f'/nacimiento/reporte/{report.pk}/lectura-estado/',
        'reveal_url':    f'/nacimiento/reporte/{report.pk}/revelar/',
        'back_url':      reverse(back_view, args=[report.pk]),
    })


@login_required
def astral_lectura(request, pk):
    return _birth_lectura_view(request, pk, BirthReport.TYPE_ASTRAL)


@login_required
def hd_lectura(request, pk):
    return _birth_lectura_view(request, pk, BirthReport.TYPE_HD)


@login_required
def saju_lectura(request, pk):
    return _birth_lectura_view(request, pk, BirthReport.TYPE_SAJU)


@login_required
def birth_insight_reveal(request, pk):
    if request.method != 'POST':
        return redirect('birth:profile')
    report = get_object_or_404(BirthReport, pk=pk, user=request.user)

    if report.interpretation and report.interpretation != 'processing':
        lectura_name = _BIRTH_LECTURA_NAMES.get(report.report_type, 'profile')
        return redirect(f'birth:{lectura_name}', pk=pk)

    try:
        bp = request.user.birth_profile
    except BirthProfile.DoesNotExist:
        return redirect('birth:profile')

    try:
        from tokens.models import TokenBalance
        balance, _ = TokenBalance.objects.get_or_create(
            user=request.user, defaults={'balance': 50}
        )
        label = _BIRTH_TYPE_LABELS.get(report.report_type, 'Lectura')
        balance.spend(5, reason=f'Lectura endonauta — {label}')
    except Exception:
        pass

    BirthReport.objects.filter(pk=pk).update(
        interpretation='processing',
        status=BirthReport.STATUS_PROCESSING,
    )
    fn = _BIRTH_ASYNC_FNS.get(report.report_type)
    if fn:
        threading.Thread(target=fn, args=[report.pk, bp.birth_place], daemon=True).start()

    lectura_name = _BIRTH_LECTURA_NAMES.get(report.report_type, 'profile')
    return redirect(f'birth:{lectura_name}', pk=pk)


@login_required
def birth_insight_status(request, pk):
    report = get_object_or_404(BirthReport, pk=pk, user=request.user)
    if report.interpretation in ('', 'processing'):
        return JsonResponse({'status': 'processing'})
    if report.status == BirthReport.STATUS_FAILED:
        return JsonResponse({'status': 'failed'})
    return JsonResponse({'status': 'complete', 'interpretation': report.interpretation})
