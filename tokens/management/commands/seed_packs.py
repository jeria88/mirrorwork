"""
Crear/actualizar los packs de fractones iniciales.
Uso: python3 manage.py seed_packs
"""
from django.core.management.base import BaseCommand
from tokens.models import TokenPack


class Command(BaseCommand):
    help = "Crea o actualiza los packs de fractones iniciales"

    def handle(self, *args, **options):
        packs = [
            {"slug": "starter",    "name": "Starter",    "fractones": 10, "price_clp": 1990,  "price_usd": 2.99, "order": 1},
            {"slug": "explorador", "name": "Explorador", "fractones": 25, "price_clp": 3990,  "price_usd": 4.99, "order": 2},
            {"slug": "viajero",    "name": "Viajero",    "fractones": 60, "price_clp": 7990,  "price_usd": 9.99, "order": 3},
        ]
        for p in packs:
            pack, created = TokenPack.objects.update_or_create(
                slug=p["slug"],
                defaults=p,
            )
            action = "Creado" if created else "Actualizado"
            self.stdout.write(f"  {action}: {pack}")

        self.stdout.write(self.style.SUCCESS(f"{len(packs)} packs listos"))
