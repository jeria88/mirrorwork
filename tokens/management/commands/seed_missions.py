"""
python3 manage.py seed_missions

Crea o actualiza las misiones iniciales de MirrorWork.
"""
from django.core.management.base import BaseCommand

from tokens.models import Mission

MISSIONS = [
    {
        'slug': 'onboarding',
        'name': 'Primer paso',
        'description': 'Completa el onboarding y define tu punto de entrada al viaje.',
        'fracton_reward': 60,
        'order': 1,
    },
    {
        'slug': 'first_test',
        'name': 'Primera exploración',
        'description': 'Completa tu primer test psicométrico.',
        'fracton_reward': 20,
        'order': 2,
    },
    {
        'slug': 'first_espejo',
        'name': 'Primera reflexión',
        'description': 'Inicia tu primera sesión con el Espejo de Conflictos.',
        'fracton_reward': 40,
        'order': 3,
    },
    {
        'slug': 'first_dimension',
        'name': 'Dimensión iluminada',
        'description': 'Completa todos los tests de una dimensión de tu mapa interior.',
        'fracton_reward': 50,
        'order': 4,
    },
]


class Command(BaseCommand):
    help = 'Crea o actualiza las misiones iniciales'

    def handle(self, *args, **options):
        for data in MISSIONS:
            obj, created = Mission.objects.update_or_create(
                slug=data['slug'],
                defaults=data,
            )
            status = 'creada' if created else 'actualizada'
            self.stdout.write(f'  {obj.name} — {status} (+{obj.fracton_reward})')
        self.stdout.write(self.style.SUCCESS(f'{len(MISSIONS)} misiones listas'))
