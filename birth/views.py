import json
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


# ── Diccionarios de descripción para hd_detail ───────────────────────────────

_HD_TYPE_DESCS = {
    'Generador': 'Eres el motor de la humanidad: energía vital sostenida que, cuando se usa bien, no se agota. Tu sistema está diseñado para responder, no para iniciar. Cuando esperás la señal del entorno antes de comprometerte, la energía fluye sin fricción.',
    'Generador Manifestante': 'Combinás la energía motriz del Generador con la capacidad iniciadora del Manifestante. Podés iniciar Y responder, pero los demás necesitan saber qué estás haciendo antes de que lo hagas — sin eso, tu movimiento genera resistencia en lugar de apoyo.',
    'Manifestador': 'Sos el único tipo diseñado para iniciar. Tu energía es un impacto: comienza en vos y se irradia al entorno. Informar a quienes te rodean antes de actuar no es pedir permiso — es reducir la resistencia para que tu impulso llegue completo.',
    'Proyector': 'Sos un guía de energía, no un generador de ella. Tenés una capacidad inusual para leer a los demás y ver el todo del sistema. Tu diseño funciona con la invitación genuina: cuando alguien te reconoce y te convoca, la energía se alinea. Sin ese reconocimiento previo, el esfuerzo se convierte en agotamiento.',
    'Reflector': 'Sos el espejo de la comunidad que te rodea — reflejás el estado colectivo del entorno con una claridad extraordinaria. Tu ciclo natural de decisión es el mes lunar: las decisiones tomadas en un día no aprovechan tu sabiduría más profunda. El entorno donde vivís importa más que para cualquier otro tipo.',
}

_HD_STRATEGY_DESCS = {
    'Responder (esperar una señal del entorno)': 'No inicies desde el pensamiento. Esperá que algo externo aparezca — una pregunta, una situación, una oportunidad — y observá la respuesta espontánea del cuerpo antes de comprometerte. El sí o el no viene antes que las razones.',
    'Responder y luego informar antes de actuar': 'Primero escuchá la respuesta del cuerpo ante lo que el entorno trae. Una vez que hay un sí claro, informá a las personas clave de tu entorno antes de iniciar — no para pedir permiso, sino para que tu movimiento no llegue como una sorpresa.',
    'Informar antes de actuar': 'Antes de iniciar algo, informá a las personas de tu entorno inmediato. No es pedir autorización — es preparar el terreno para que tu impacto no genere resistencia automática.',
    'Esperar la invitación': 'En las áreas clave de vida — trabajo, amor, lugar donde vivís — esperá que alguien te reconozca y te invite a participar. Sin ese reconocimiento previo, tu energía se dispersa y genera amargura. La calidad de la invitación importa.',
    'Esperar un ciclo lunar completo (29 días)': 'Para decisiones importantes, esperá un ciclo lunar completo antes de comprometerte. Cada día del ciclo te da una perspectiva diferente sobre la misma pregunta. La claridad no es intelectual — emerge a lo largo del tiempo.',
}

_HD_AUTHORITY_DESCS = {
    'Sacral': 'Tu autoridad vive en las tripas: un "uh-huh" espontáneo o un "unh-unh" es tu guía más confiable. No es una decisión razonada — es una respuesta inmediata que viene antes del pensamiento. Si necesitás preguntarte dos veces, el Sacral ya respondió.',
    'Emocional — Plexo Solar': 'No hay claridad en el momento emocional. La regla es simple: esperar la ola. Ni el punto más alto (euforia) ni el más bajo (depresión) son el momento para decidir. La claridad llega cuando la ola encuentra su meseta — con el tiempo, no con la urgencia.',
    'Esplénico — Bazo': 'Es la autoridad más antigua y sutil: una voz instintiva, en el momento presente. Habla una sola vez — si necesitás repetirte la señal, ya no viene del Bazo. Requiere confiar en lo que se siente en el instante, antes de que el miedo o la mente intervengan.',
    'Ego — Corazón': 'Tu autoridad viene del corazón y la voluntad. Escuchás lo que realmente querés vs. lo que sentís que "deberías" querer. Si no hay un "yo quiero" genuino en la respuesta, no es correcto para vos. La voluntad propia no es egoísmo — es tu brújula.',
    'Identidad — G': 'Tu autoridad es el entorno. La claridad llega cuando encontrás el espacio físico, las personas y las conversaciones correctas. Hablar tu proceso en voz alta con personas que te escuchan sin juzgar — y observar qué emerge — es tu camino de decisión.',
    'Mental — Externo': 'No hay autoridad interna definida. Las decisiones se clarifican verbalizando: hablar con distintas personas de confianza no para que te aconsejen, sino para escucharte hablar y notar qué resuena en tu cuerpo. El entorno exterior es tu espejo de claridad.',
    'Lunar — 29 días': 'Tu autoridad es el ciclo lunar completo. Ninguna decisión importante se toma antes de haber observado cómo te sentís al respecto durante un mes entero. Consultás con personas distintas en distintos momentos del ciclo para recibir perspectivas variadas.',
}

_HD_PROFILE_LINE_DESCS = {
    '1': 'La Línea 1 necesita base. Investigás, estudiás, te preparás antes de sentirte seguro/a para actuar. La inseguridad surge cuando no tenés suficiente fundamento — y esa inseguridad es real, no exagerada. Es una señal de que falta investigación.',
    '2': 'La Línea 2 tiene dones naturales que a menudo no ve en sí misma. Necesita tiempo a solas para integrar lo que sabe. Generalmente es llamada por otros antes de sentirse "lista" — y esa llamada desde afuera puede ser la señal de que es momento de salir.',
    '3': 'La Línea 3 aprende a través del ensayo y el error. Los "fracasos" son parte del diseño, no señales de estar equivocado/a. Cada experiencia que no funciona deja una sabiduría práctica que ningún libro puede enseñar. La vida como laboratorio.',
    '4': 'La Línea 4 construye a través de relaciones y redes. Las oportunidades más importantes llegan a través de personas ya conocidas, no de desconocidos. La fundación de la vida es la calidad de los vínculos cercanos.',
    '5': 'La Línea 5 es proyectada por los demás como el "salvador práctico" — alguien que tiene soluciones para lo que otros no pueden resolver. Las expectativas externas pueden ser una trampa: aprender a discernir cuándo responder al llamado y cuándo no es el trabajo central.',
    '6': 'La Línea 6 tiene tres etapas de vida claramente distintas: los primeros 30 años son de aprendizaje intenso (a menudo doloroso); los siguientes 20 de retiro y observación; después de los 50, emerge como modelo de rol genuino — alguien que vivió lo que enseña.',
}

_HD_DEFINITION_DESCS = {
    'Indefinido': 'Sin centros definidos, toda tu energía viene del entorno. Sos altamente sensible a las personas y lugares que te rodean — y podés amplificar y reflejar la energía de quienes están cerca con una claridad extraordinaria. El entorno donde vivís y trabajás importa profundamente.',
    'Definición Simple': 'Toda tu energía está conectada en un solo circuito interno. Sos consistente, predecible y relativamente independiente del entorno para funcionar. La sombra: puede ser difícil absorber nuevas perspectivas que no encajan fácilmente con la estructura ya definida.',
    'Definición Partida': 'Tenés dos circuitos de energía separados que no se conectan internamente. La brecha entre ellos es un punto de búsqueda inconsciente: tendés a encontrar personas o situaciones que "completen" esa conexión — lo cual puede llevar a dependencias o relaciones de completitud en lugar de elección.',
    'Definición Partida Triple': 'Tres circuitos separados que operan de manera independiente. Sos adaptable y versátil — podés conectar con tipos muy distintos de personas y sistemas. La consistencia interna es menor, pero la capacidad de tender puentes entre mundos diferentes es mayor.',
    'Definición Cuádruple': 'Cuatro circuitos completamente separados. La adaptabilidad es máxima — cada circuito puede resonar con personas y contextos muy distintos. La experiencia interna puede sentirse fragmentada, pero es en realidad una flexibilidad extraordinaria que pocos comprenden.',
}

_HD_NOT_SELF_DESCS = {
    'Frustración': 'La frustración es la señal de que estás operando fuera de tu diseño — iniciando en lugar de esperar a responder, o comprometiendo energía donde no hay un sí genuino del cuerpo. No es algo a eliminar: es información sobre dónde la estrategia está siendo ignorada.',
    'Frustración / Ira': 'La frustración señala que estás iniciando sin responder primero. La ira indica que estás actuando sin informar. Ambas son avisos del cuerpo — no emociones a suprimir, sino señales de que el diseño no está siendo escuchado.',
    'Ira': 'La ira aparece cuando actuás sin informar a tu entorno. No es que hiciste algo malo — es que el impacto de tu movimiento llegó sin preparación al campo de los demás, y eso genera resistencia automática. La ira es la señal de que faltó el paso de informar.',
    'Amargura': 'La amargura surge cuando actuás sin invitación, cuando te esforzás sin que nadie te haya reconocido genuinamente, o cuando esperás más de lo que el entorno puede darte. Es la señal de que la estrategia de esperar el reconocimiento está siendo evitada.',
    'Decepción': 'La decepción es la señal del Reflector de que está en un entorno que no lo nutre, o tomando decisiones sin haber esperado el ciclo lunar completo. Es la brújula que indica que algo en el campo externo o en el ritmo interno está fuera de alineación.',
}

_HD_SIGNATURE_DESCS = {
    'Satisfacción': 'La satisfacción no siempre es euforia — puede ser el simple placer de un trabajo que vale la pena, la sensación de que la energía fue bien usada. Es la confirmación interior de que el cuerpo respondió sí, y el compromiso honró esa respuesta.',
    'Paz y satisfacción': 'La paz llega cuando el movimiento fue claro e informado. La satisfacción cuando la energía fue bien respondida y usada. Juntas, señalan que el diseño está siendo vivido — no la tranquilidad de no hacer nada, sino la de actuar desde el lugar correcto.',
    'Paz': 'La paz no es resignación — es la quietud de quien actúa desde el momento correcto y sin imponer. Es la señal de que el impacto fue honrado y que el informar creó espacio en lugar de resistencia.',
    'Éxito': 'El éxito del Proyector no es acumulación — es el reconocimiento genuino de que tu guía fue escuchada y que aportaste claridad donde otros no podían verla. No el éxito como validación social, sino como evidencia de que fuiste invitado/a e hiciste lo que mejor sabés hacer.',
    'Sorpresa': 'El deleite del Reflector es la rareza de encontrarse completamente sorprendido/a — sin expectativas cristalizadas, abierto/a a lo imprevisto como modo de vida. Es la señal de que el entorno es correcto y de que el ciclo de la luna está siendo respetado.',
}


# ── Configuraciones de secciones para lectura.html ───────────────────────────

_SECTION_CONFIGS = {
    'astral': [
        {'icon': '☉', 'label': 'El Sol y la Identidad', 'color': '#f0c040'},
        {'icon': '☽', 'label': 'La Luna y las Emociones', 'color': '#7c6dfa'},
        {'icon': '⬡', 'label': 'El Ascendente y los Vínculos', 'color': '#4ecdc4'},
        {'icon': '◉', 'label': 'El Patrón y la Sombra', 'color': '#e05050'},
        {'icon': '✦', 'label': 'La Invitación Actual', 'color': '#f4a035'},
    ],
    'hd': [
        {'icon': '◈', 'label': 'Tipo y Estrategia en la Vida', 'color': '#4ecdc4'},
        {'icon': '○', 'label': 'La Autoridad Interior', 'color': '#7c6dfa'},
        {'icon': '◇', 'label': 'El Perfil y el Rol de Vida', 'color': '#f4a035'},
        {'icon': '☯', 'label': 'Las Puertas del Sol', 'color': '#f0c040'},
        {'icon': '⬤', 'label': 'Centros y el Tema No-Yo', 'color': '#e05050'},
    ],
    'saju': [
        {'icon': '◎', 'label': 'El Maestro del Día', 'color': '#f4a035'},
        {'icon': '⬡', 'label': 'El Balance Elemental', 'color': '#4ecdc4'},
        {'icon': '◈', 'label': 'El Animal del Año', 'color': '#7c6dfa'},
        {'icon': '◉', 'label': 'Las Tensiones Internas', 'color': '#e05050'},
        {'icon': '✦', 'label': 'El Ciclo Vital Actual', 'color': '#f0c040'},
    ],
}


def _parse_lectura_sections(text, configs):
    if not text or text == 'processing':
        return []
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    result = []
    for i, cfg in enumerate(configs):
        if i < len(paras):
            result.append({**cfg, 'text': paras[i]})
    for extra in paras[len(configs):]:
        result.append({
            'icon': '◎',
            'label': 'Pregunta de exploración',
            'color': '#7c6dfa',
            'text': extra,
            'is_question': True,
        })
    return result


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
    chart = report.chart_data or {}
    profile_line = (chart.get('profile') or '')[0] if chart.get('profile') else ''
    hd_descs = {
        'type':       _HD_TYPE_DESCS.get(chart.get('type', ''), ''),
        'strategy':   _HD_STRATEGY_DESCS.get(chart.get('strategy', ''), ''),
        'authority':  _HD_AUTHORITY_DESCS.get(chart.get('authority', ''), ''),
        'profile':    _HD_PROFILE_LINE_DESCS.get(profile_line, ''),
        'definition': _HD_DEFINITION_DESCS.get(chart.get('definition', ''), ''),
        'not_self':   _HD_NOT_SELF_DESCS.get(chart.get('not_self_theme', ''), ''),
        'signature':  _HD_SIGNATURE_DESCS.get(chart.get('signature', ''), ''),
    }
    return render(request, 'birth/hd_detail.html', {
        'report': report, 'bp': bp,
        'poll_url': f'/nacimiento/reporte/{report.pk}/estado/',
        'hd_descs': hd_descs,
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

_REPORT_TYPE_KEYS = {
    BirthReport.TYPE_ASTRAL: 'astral',
    BirthReport.TYPE_HD:     'hd',
    BirthReport.TYPE_SAJU:   'saju',
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
    type_key  = _REPORT_TYPE_KEYS.get(report_type, 'astral')
    sec_cfg   = _SECTION_CONFIGS.get(type_key, [])
    sections  = _parse_lectura_sections(report.interpretation, sec_cfg) if is_revealed else []
    return render(request, 'birth/lectura.html', {
        'report':               report,
        'label':                _BIRTH_TYPE_LABELS.get(report_type, ''),
        'is_processing':        is_processing,
        'is_revealed':          is_revealed,
        'poll_url':             f'/nacimiento/reporte/{report.pk}/lectura-estado/',
        'reveal_url':           f'/nacimiento/reporte/{report.pk}/revelar/',
        'back_url':             reverse(back_view, args=[report.pk]),
        'sections':             sections,
        'sections_config_json': json.dumps(sec_cfg, ensure_ascii=False),
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
