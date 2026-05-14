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
HD_GATES = [
    25,17,21,51,42, 3,27,24, 2,23, 8,20,16,35,45,12,
    15,52,39,53,62,56,31,33, 7, 4,29,59,40,64,47, 6,
    46,18,48,57,32,50,28,44, 1,43,14,34, 9, 5,26,11,
    10,58,38,54,61,60,41,19,13,49,30,55,37,63,22,36,
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

# 36 channels: (gate_a, gate_b) — a channel is active if both gates are active
HD_CHANNELS = [
    (64,47),(61,24),(63,4),(17,62),(43,23),(11,56),(31,7),(8,1),(33,13),
    (20,10),(20,34),(45,21),(2,14),(46,29),(59,6),(27,50),(3,60),(9,52),
    (5,15),(29,46),(42,53),(53,19),(39,55),(35,36),(37,40),(22,12),(36,35),
    (30,41),(41,30),(19,49),(49,19),(18,58),(48,16),(57,34),(32,54),(28,38),
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
        zodiac_type='Tropic',
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


def _build_astral_prompt(chart_data, birth_place):
    planets = chart_data['planets']
    sun = next(p for p in planets if p['key'] == 'sun')
    moon = next(p for p in planets if p['key'] == 'moon')
    asc = chart_data['ascendant']

    lines = [f"  - {p['label']}: {p['sign']} (Casa {p['house']}){' ℞' if p['retrograde'] else ''}"
             for p in planets]
    tabla = '\n'.join(lines)

    return (
        f"Eres el Espejo Endonauta. Un usuario nacido en {birth_place} acaba de recibir su carta astral.\n\n"
        f"Sus tres puntos cardinales: Sol en {sun['sign']} (Casa {sun['house']}), "
        f"Luna en {moon['sign']} (Casa {moon['house']}), Ascendente en {asc['sign']}.\n\n"
        f"Posiciones completas:\n{tabla}\n\n"
        "Escribe una lectura endonauta de 4-5 párrafos. No diagnostiques. Conecta cada posición "
        "con el viaje interior del usuario, usando el lenguaje de las dimensiones endonautas "
        "(identidad, sombra, cuerpo, emociones, mente, propósito, espiritualidad, vínculos, "
        "creatividad, comunidad, sueños, abundancia) cuando sea natural. "
        "Termina con una pregunta de exploración. Tono cálido, curioso, empoderador. En español. "
        "Formato: párrafos separados por salto de línea, sin títulos ni bullets."
    )


def _generate_interpretation_async(report_pk, birth_place):
    from django.db import connection
    connection.close()

    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not api_key:
        BirthReport.objects.filter(pk=report_pk).update(
            status=BirthReport.STATUS_FAILED
        )
        return

    try:
        report = BirthReport.objects.get(pk=report_pk)
        prompt = _build_astral_prompt(report.chart_data, birth_place)

        resp = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.75,
                'max_tokens': 800,
            },
            timeout=40,
        )
        resp.raise_for_status()
        text = resp.json()['choices'][0]['message']['content']
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
            'status': BirthReport.STATUS_PROCESSING,
            'interpretation': '',
        },
    )

    has_tokens = False
    try:
        from tokens.models import TokenBalance
        balance, _ = TokenBalance.objects.get_or_create(
            user=request.user, defaults={'balance': 50}
        )
        has_tokens = balance.spend(5, reason='Interpretación carta astral')
    except Exception:
        pass

    if has_tokens:
        t = threading.Thread(
            target=_generate_interpretation_async,
            args=[report.pk, bp.birth_place],
            daemon=True,
        )
        t.start()
    else:
        report.status = BirthReport.STATUS_COMPLETE
        report.save(update_fields=['status', 'updated_at'])

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
    gate_size = 360 / 64
    idx = int(lon / gate_size) % 64
    gate = HD_GATES[idx]
    line = int((lon % gate_size) / (gate_size / 6)) + 1
    return gate, min(line, 6)


def _calculate_hd_chart(bp):
    from kerykeion import AstrologicalSubject

    hour = bp.birth_time.hour if bp.birth_time else 12
    minute = bp.birth_time.minute if bp.birth_time else 0
    lat = bp.latitude or 0.0
    lng = bp.longitude or 0.0
    tz = bp.timezone_str or 'UTC'

    # Personality (birth moment)
    p = AstrologicalSubject('p', bp.birth_date.year, bp.birth_date.month, bp.birth_date.day,
                            hour, minute, lat=lat, lng=lng, tz_str=tz, zodiac_type='Tropic')

    p_sun_g, p_sun_l   = _lon_to_gate_line(p.sun.abs_pos)
    p_earth_g, p_earth_l = _lon_to_gate_line((p.sun.abs_pos + 180) % 360)
    p_moon_g, p_moon_l   = _lon_to_gate_line(p.moon.abs_pos)
    p_nodes = {
        'mercury': _lon_to_gate_line(p.mercury.abs_pos),
        'venus':   _lon_to_gate_line(p.venus.abs_pos),
        'mars':    _lon_to_gate_line(p.mars.abs_pos),
        'jupiter': _lon_to_gate_line(p.jupiter.abs_pos),
        'saturn':  _lon_to_gate_line(p.saturn.abs_pos),
        'uranus':  _lon_to_gate_line(p.uranus.abs_pos),
        'neptune': _lon_to_gate_line(p.neptune.abs_pos),
        'pluto':   _lon_to_gate_line(p.pluto.abs_pos),
    }

    # Design (~88° before birth ≈ 89 days)
    design_date = bp.birth_date - timedelta(days=89)
    d = AstrologicalSubject('d', design_date.year, design_date.month, design_date.day,
                            12, 0, lat=lat, lng=lng, tz_str=tz, zodiac_type='Tropic')

    d_sun_g, d_sun_l   = _lon_to_gate_line(d.sun.abs_pos)
    d_earth_g, d_earth_l = _lon_to_gate_line((d.sun.abs_pos + 180) % 360)

    # All active gates (Personality + Design, all planets)
    active_gates = set()
    active_gates.update([p_sun_g, p_earth_g, p_moon_g, d_sun_g, d_earth_g])
    for g, _ in p_nodes.values():
        active_gates.add(g)
    for planet in [d.mercury, d.venus, d.mars, d.jupiter, d.saturn, d.uranus, d.neptune, d.pluto]:
        g, _ = _lon_to_gate_line(planet.abs_pos)
        active_gates.add(g)
    for planet in [d.moon]:
        g, _ = _lon_to_gate_line(planet.abs_pos)
        active_gates.add(g)

    # Defined centers
    defined_centers = set()
    for center, gates in HD_CENTER_GATES.items():
        if any(g in active_gates for g in gates):
            defined_centers.add(center)

    # Approximate type
    sacral_defined = 'Sacral' in defined_centers or any(
        g in active_gates for g in HD_CENTER_GATES['Sacral']
    )
    throat_motors = set()
    motor_centers = {'Corazón', 'Plexo Solar', 'Raíz', 'Sacral'}
    for ch in HD_CHANNELS:
        g_a, g_b = ch
        ctr_a = next((c for c, gs in HD_CENTER_GATES.items() if g_a in gs), None)
        ctr_b = next((c for c, gs in HD_CENTER_GATES.items() if g_b in gs), None)
        if g_a in active_gates and g_b in active_gates:
            if ctr_a == 'Garganta' and ctr_b in motor_centers:
                throat_motors.add(ctr_b)
            if ctr_b == 'Garganta' and ctr_a in motor_centers:
                throat_motors.add(ctr_a)

    if sacral_defined and throat_motors - {'Sacral'}:
        hd_type = 'Generador Manifestante'
        strategy = 'Responder y luego informar antes de actuar'
        not_self = 'Frustración'
    elif sacral_defined:
        hd_type = 'Generador'
        strategy = 'Responder (esperar una señal del entorno)'
        not_self = 'Frustración'
    elif throat_motors:
        hd_type = 'Manifestador'
        strategy = 'Informar antes de actuar'
        not_self = 'Ira'
    else:
        all_defined = len(defined_centers)
        if all_defined == 0:
            hd_type = 'Reflector'
            strategy = 'Esperar un ciclo lunar completo (29 días)'
            not_self = 'Decepción'
        else:
            hd_type = 'Proyector'
            strategy = 'Esperar la invitación'
            not_self = 'Amargura'

    profile = HD_PROFILES.get(
        (p_sun_l, p_earth_l),
        f'{p_sun_l}/{p_earth_l}'
    )

    return {
        'personality': {
            'sun':   {'gate': p_sun_g,   'line': p_sun_l,   'name': HD_GATE_NAMES.get(p_sun_g, '')},
            'earth': {'gate': p_earth_g, 'line': p_earth_l, 'name': HD_GATE_NAMES.get(p_earth_g, '')},
            'moon':  {'gate': p_moon_g,  'line': p_moon_l,  'name': HD_GATE_NAMES.get(p_moon_g, '')},
        },
        'design': {
            'sun':   {'gate': d_sun_g,   'line': d_sun_l,   'name': HD_GATE_NAMES.get(d_sun_g, '')},
            'earth': {'gate': d_earth_g, 'line': d_earth_l, 'name': HD_GATE_NAMES.get(d_earth_g, '')},
        },
        'profile':          profile,
        'type':             hd_type,
        'strategy':         strategy,
        'not_self_theme':   not_self,
        'defined_centers':  sorted(defined_centers),
        'active_gates':     sorted(active_gates),
        'design_date':      design_date.strftime('%Y-%m-%d'),
    }


def _build_hd_prompt(chart_data, birth_place):
    p = chart_data['personality']
    d = chart_data['design']
    return (
        f"Eres el Espejo Endonauta. Un usuario nacido en {birth_place} acaba de recibir su chart de Diseño Humano.\n\n"
        f"Tipo: {chart_data['type']}\n"
        f"Estrategia: {chart_data['strategy']}\n"
        f"Perfil: {chart_data['profile']}\n"
        f"Tema No-Yo: {chart_data['not_self_theme']}\n\n"
        f"Puerta Personalidad Sol: {p['sun']['gate']} — {p['sun']['name']} (Línea {p['sun']['line']})\n"
        f"Puerta Personalidad Tierra: {p['earth']['gate']} — {p['earth']['name']} (Línea {p['earth']['line']})\n"
        f"Puerta Diseño Sol: {d['sun']['gate']} — {d['sun']['name']} (Línea {d['sun']['line']})\n"
        f"Puerta Diseño Tierra: {d['earth']['gate']} — {d['earth']['name']} (Línea {d['earth']['line']})\n"
        f"Centros definidos: {', '.join(chart_data['defined_centers'])}\n\n"
        "Escribe una lectura endonauta de 4-5 párrafos. Conecta el Tipo, la Estrategia y el Perfil con "
        "el viaje interior del usuario. Explica qué significa su estrategia en la vida cotidiana. "
        "Conecta con las dimensiones endonautas (identidad, propósito, vínculos, creatividad). "
        "Termina con una pregunta de exploración. Tono cálido, empoderador, sin jerga técnica. En español. "
        "Formato: párrafos separados por salto de línea, sin títulos ni bullets."
    )


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
        resp = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': prompt}],
                  'temperature': 0.75, 'max_tokens': 800},
            timeout=40,
        )
        resp.raise_for_status()
        report.interpretation = resp.json()['choices'][0]['message']['content']
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
        defaults={'chart_data': chart_data, 'status': BirthReport.STATUS_PROCESSING, 'interpretation': ''},
    )

    has_tokens = False
    try:
        from tokens.models import TokenBalance
        balance, _ = TokenBalance.objects.get_or_create(user=request.user, defaults={'balance': 50})
        has_tokens = balance.spend(5, reason='Interpretación Diseño Humano')
    except Exception:
        pass

    if has_tokens:
        t = threading.Thread(target=_generate_hd_async, args=[report.pk, bp.birth_place], daemon=True)
        t.start()
    else:
        report.status = BirthReport.STATUS_COMPLETE
        report.save(update_fields=['status', 'updated_at'])

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

def _birth_hour_to_shichen(hour):
    """Convert 24h hour to the 12 traditional Chinese time periods (each 2h)."""
    return hour // 2


def _calculate_saju_chart(bp):
    import sxtwl

    d = sxtwl.fromSolar(bp.birth_date.year, bp.birth_date.month, bp.birth_date.day)
    yr = d.getYearGZ(True)
    mo = d.getMonthGZ()
    dy = d.getDayGZ()

    hour = bp.birth_time.hour if bp.birth_time else None
    hr_gz = sxtwl.getShiGz(dy.tg, hour if hour is not None else 12)

    def gz_info(gz, label):
        return {
            'label':   label,
            'stem':    TIANGAN[gz.tg],
            'branch':  DIZHI[gz.dz],
            'rom_stem': TIAN_ROM[gz.tg],
            'rom_branch': DI_ROM[gz.dz],
            'elem_stem':  TIAN_ES[gz.tg],
            'animal':  DI_ANIMAL[gz.dz],
            'elem_branch': DI_ELEM[gz.dz],
        }

    pillars = [
        gz_info(yr, 'Año'),
        gz_info(mo, 'Mes'),
        gz_info(dy, 'Día'),
        gz_info(hr_gz, 'Hora'),
    ]

    # Element count
    elem_count = {}
    for p in pillars:
        for e in [p['elem_stem'].split()[0], p['elem_branch']]:
            elem_count[e] = elem_count.get(e, 0) + 1

    dominant = max(elem_count, key=elem_count.get)
    weakest  = min(elem_count, key=elem_count.get) if len(elem_count) > 1 else None

    # Day Master (pilar día tallo celestial = identidad central)
    day_master_stem = TIAN_ES[dy.tg]

    return {
        'pillars':         pillars,
        'element_count':   elem_count,
        'dominant_element': dominant,
        'weakest_element':  weakest,
        'day_master':      day_master_stem,
        'hour_known':      bp.birth_time is not None,
        'lunar_year_animal': DI_ANIMAL[yr.dz],
    }


def _build_saju_prompt(chart_data, birth_place):
    pillars = chart_data['pillars']
    p_text = '\n'.join(
        f"  {p['label']}: {p['stem']}({p['rom_stem']}/{p['elem_stem']}) "
        f"{p['branch']}({p['rom_branch']}/{p['animal']}/{p['elem_branch']})"
        for p in pillars
    )
    return (
        f"Eres el Espejo Endonauta. Un usuario nacido en {birth_place} acaba de recibir su carta Saju.\n\n"
        f"Maestro del Día (identidad central): {chart_data['day_master']}\n"
        f"Animal del año lunar: {chart_data['lunar_year_animal']}\n"
        f"Elemento dominante: {chart_data['dominant_element']}\n"
        f"Elemento más débil: {chart_data.get('weakest_element', 'equilibrado')}\n\n"
        f"Los Cuatro Pilares:\n{p_text}\n\n"
        "Escribe una lectura endonauta de 4-5 párrafos basada en los Cuatro Pilares del Destino (사주). "
        "Explica el Maestro del Día como la energía central de la persona. "
        "Conecta el elemento dominante y el más débil con áreas de fortaleza y crecimiento. "
        "Menciona el animal del año y lo que aporta. "
        "Conecta con las dimensiones endonautas cuando sea natural. "
        "Termina con una pregunta de exploración. Tono cálido, curioso. En español. "
        "Sin jerga técnica china innecesaria. Párrafos separados por salto de línea."
    )


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
        resp = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': prompt}],
                  'temperature': 0.75, 'max_tokens': 800},
            timeout=40,
        )
        resp.raise_for_status()
        report.interpretation = resp.json()['choices'][0]['message']['content']
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
        defaults={'chart_data': chart_data, 'status': BirthReport.STATUS_PROCESSING, 'interpretation': ''},
    )

    has_tokens = False
    try:
        from tokens.models import TokenBalance
        balance, _ = TokenBalance.objects.get_or_create(user=request.user, defaults={'balance': 50})
        has_tokens = balance.spend(5, reason='Interpretación Saju')
    except Exception:
        pass

    if has_tokens:
        t = threading.Thread(target=_generate_saju_async, args=[report.pk, bp.birth_place], daemon=True)
        t.start()
    else:
        report.status = BirthReport.STATUS_COMPLETE
        report.save(update_fields=['status', 'updated_at'])

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
