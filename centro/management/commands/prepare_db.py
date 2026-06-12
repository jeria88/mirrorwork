from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Corrige BD inconsistente (tablas parciales) y resuelve conflictos de migración para cuentas unificadas'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)

            # 1. Resolver conflicto de InconsistentMigrationHistory (transición a custom User model)
            if 'django_migrations' in tables:
                cursor.execute("SELECT id FROM django_migrations WHERE app = 'admin'")
                admin_applied = cursor.fetchone()
                cursor.execute("SELECT id FROM django_migrations WHERE app = 'accounts'")
                accounts_applied = cursor.fetchone()

                if admin_applied and not accounts_applied:
                    self.stdout.write(self.style.WARNING(
                        "prepare_db: Detectado conflicto de migración (admin aplicado sin accounts)."
                    ))
                    self.stdout.write(self.style.WARNING(
                        "Resolviendo conflicto: eliminando registros de migración de 'admin' y 'auth' para permitir --fake-initial."
                    ))
                    cursor.execute("DELETE FROM django_migrations WHERE app IN ('admin', 'auth')")
                    self.stdout.write(self.style.SUCCESS("prepare_db: Registros de admin/auth eliminados."))

            if 'auth_user' in tables:
                self.stdout.write(self.style.SUCCESS('prepare_db: BD OK'))
                return

            self.stdout.write(self.style.WARNING(
                'prepare_db: auth_user ausente — reseteando schema public para migrate limpio'
            ))
            cursor.execute("DROP SCHEMA public CASCADE")
            cursor.execute("CREATE SCHEMA public")
            cursor.execute("GRANT ALL ON SCHEMA public TO public")
            self.stdout.write(self.style.SUCCESS('prepare_db: schema reseteado'))
