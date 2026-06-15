from django.core.management.base import BaseCommand
from wagtail.models import Page, Site
from home.models import HomePage


class Command(BaseCommand):
    help = 'Crea HomePage de Wagtail y configura el Site (idempotente)'

    def handle(self, *args, **options):
        # Si ya existe HomePage viva, solo verificar/actualizar Site
        home = HomePage.objects.filter(live=True).first()
        
        default_magnets = [
            ('lead_magnet', {
                'magnet_type': 'mascara',
                'headline': '¿Qué máscara usas para protegerte del rechazo?',
                'cta_text': 'Iniciar Test de Máscaras →',
                'brevo_list_id': 7,
            }),
            ('lead_magnet', {
                'magnet_type': 'hacks',
                'headline': 'Tres atajos para desactivar la autoexigencia.',
                'cta_text': 'Descargar Guía →',
                'brevo_list_id': 5,
            }),
            ('lead_magnet', {
                'magnet_type': 'viaje',
                'headline': 'Un recorrido somático de 7 días.',
                'cta_text': 'Empezar el Viaje →',
                'brevo_list_id': 6,
            }),
            ('lead_magnet', {
                'magnet_type': 'endonautica',
                'headline': 'Endonáutica: El Manual del Viajero Interior.',
                'cta_text': 'Ver detalles del Libro →',
                'hotmart_url': 'https://endonautas.cl/endonautica/',
            }),
        ]
        
        if home:
            if not home.lead_magnets:
                home.lead_magnets = default_magnets
                home.save_revision().publish()
                self.stdout.write(self.style.SUCCESS('seed_wagtail: lead_magnets creados en HomePage existente'))
            self._ensure_site(home)
            self.stdout.write(self.style.SUCCESS(f'seed_wagtail: HomePage OK (id={home.id})'))
            return

        # Borrar página de bienvenida por defecto de Wagtail si existe
        # (la que tiene título "Welcome to your new Wagtail site!")
        Page.objects.filter(depth=2, slug='home', content_type__model='page').exclude(content_type__model='homepage').delete()

        # Raíz del árbol Wagtail (siempre depth=1 tras migrate)
        root = Page.objects.filter(depth=1).first()
        if not root:
            self.stdout.write(self.style.ERROR('seed_wagtail: root page no existe — migrate primero'))
            return

        home = HomePage(
            title='Endonautas',
            slug='home',
            live=True,
            tagline='Conoce tu mundo interior con profundidad real',
            cta_app_text='Comenzar el viaje',
            cta_app_url='https://app.endonautas.cl',
            cta_ebook_text='Descargar Endonautica',
            cta_ebook_url='https://ebook.endonautas.cl',
            lead_magnets=default_magnets,
        )
        root.add_child(instance=home)
        home.save_revision().publish()

        self._ensure_site(home)
        self.stdout.write(self.style.SUCCESS(f'seed_wagtail: HomePage creada y publicada (id={home.id})'))


    def _ensure_site(self, home_page):
        Site.objects.update_or_create(
            is_default_site=True,
            defaults={
                'hostname': 'endonautas.cl',
                'port': 443,
                'site_name': 'Endonautas',
                'root_page': home_page,
            }
        )
