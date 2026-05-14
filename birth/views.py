import os
import threading

import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import BirthProfile, BirthReport, SIGN_ES, HOUSE_NUM
from .calculators import (
    calculate_astral_chart,
    calculate_hd_chart,
    calculate_saju_chart,
    ELEMENTS_ES, TIANGAN, DIZHI, TIAN_ROM, TIAN_ES,
    DI_ROM, DI_ANIMAL, DI_ELEM,
)



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


def _ensure_timezone(bp):
    """Re-derive timezone from coordinates and fix it in DB if wrong.
    Called before every chart calculation so stale 'UTC' values self-correct.
    """
    if not (bp.latitude and bp.longitude):
        return
    correct = _get_timezone(bp.latitude, bp.longitude)
    if correct != 'UTC' and bp.timezone_str != correct:
        bp.timezone_str = correct
        bp.save(update_fields=['timezone_str'])



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

    _ensure_timezone(bp)
    chart_data = calculate_astral_chart(bp)

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

    _ensure_timezone(bp)
    chart_data = calculate_hd_chart(bp)
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

    hour_known = chart_data.get('hour_known', True)
    total_chars = len(pillars) * 2
    pillar_refs = 'Mes, Día y Hora' if hour_known else 'Mes y Día'
    hora_note = '' if hour_known else '\nNOTA: La hora de nacimiento no está disponible — el Pilar de la Hora no fue calculado. El balance elemental es parcial (basado en 6 de 8 caracteres).\n'

    prompt = f"""\
SAJU — CUATRO PILARES DEL DESTINO — {birth_place}
━━━━━━━━━━━━━━━━━━━━━━━━━
MAESTRO DEL DÍA: {chart_data['day_master']} (elemento {dm_elem}, polaridad {dm_pol})
ANIMAL DEL AÑO: {chart_data['lunar_year_animal']}
{hora_note}
PILARES CALCULADOS (四柱八字):
{p_lines}

BALANCE ELEMENTAL ({total_chars} caracteres conocidos):
{elem_line}
  Dominante: {chart_data['dominant_element']} | Mínimo/ausente: {chart_data.get('weakest_element','equilibrado')}
{daewoon_block}━━━━━━━━━━━━━━━━━━━━━━━━━
{"CONTEXTO DE LA BASE DE CONOCIMIENTOS:" + chr(10) + kb + chr(10) + "━━━━━━━━━━━━━━━━━━━━━━━━━" if kb else ""}

INSTRUCCIÓN DE FORMATO — 5 párrafos en este orden exacto:

1. EL MAESTRO DEL DÍA — LA NATURALEZA CENTRAL: el Maestro del Día {chart_data['day_master']} define la energía esencial. No describas el elemento en abstracto — explica cómo se manifiesta como carácter, como forma de relacionarse con el mundo, qué tipo de fuerza interna tiene y dónde esa misma fuerza puede convertirse en rigidez o herida (dimensión Identidad/Cuerpo). Usa el elemento {dm_elem} como metáfora viva.

2. EL BALANCE ELEMENTAL — LO QUE SOBRA Y LO QUE FALTA: con {chart_data['dominant_element']} como elemento dominante y {chart_data.get('weakest_element','equilibrio') or 'equilibrio'} como el menos presente, describe qué tipo de energía gobierna la vida de esta persona y qué área de vida (emoción, relación, acción, reflexión, flujo) tiende a estar subdesarrollada. Qué prácticas o arquetipos podrían cultivar el elemento faltante (dimensión Emociones/Abundancia/Cuerpo).

3. EL ANIMAL DEL AÑO Y LOS PATRONES RELACIONALES: el {chart_data['lunar_year_animal']} como arquetipo relacional — cómo esta persona se mueve en sus vínculos, qué tipo de dinámicas tiende a atraer y qué patrón inconsciente en las relaciones refleja el animal (dimensión Vínculos/Sombra).

4. LAS TENSIONES INTERNAS — EL PATRÓN QUE SE REPITE: leyendo los pilares de {pillar_refs} (los pilares más personales disponibles), qué tensión o fricción elemental existe entre ellos. Qué conflicto interno se repite, qué patrón inconsciente emerge de esa configuración específica y cómo se manifiesta en decisiones o bloqueos recurrentes (dimensión Mente/Sombra/Creatividad).

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

    _ensure_timezone(bp)
    chart_data = calculate_saju_chart(bp)
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
