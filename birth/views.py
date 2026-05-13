import json
import os
import threading

import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import BirthProfile, BirthReport, SIGN_ES, HOUSE_NUM


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

    astral_report = BirthReport.objects.filter(
        user=request.user, report_type=BirthReport.TYPE_ASTRAL
    ).first() if bp else None

    return render(request, 'birth/birth_form.html', {
        'bp': bp,
        'astral_report': astral_report,
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
