from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Corrige BD inconsistente (tablas parciales) y resuelve conflictos de migración para cuentas unificadas'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)

            # 1. Si existe auth_user pero no accounts_user, hacemos la transición
            if 'auth_user' in tables:
                self.stdout.write(self.style.WARNING("prepare_db: auth_user detectado. Iniciando migración a accounts_user..."))
                
                # Renombrar tabla principal de usuarios
                if 'accounts_user' not in tables:
                    self.stdout.write(self.style.WARNING("Renombrando auth_user a accounts_user..."))
                    cursor.execute("ALTER TABLE auth_user RENAME TO accounts_user")
                    
                    # Intentar renombrar secuencias y restricciones si es PostgreSQL
                    if 'postgresql' in connection.settings_dict['ENGINE']:
                        try:
                            cursor.execute("ALTER SEQUENCE IF EXISTS auth_user_id_seq RENAME TO accounts_user_id_seq")
                            cursor.execute("ALTER INDEX IF EXISTS auth_user_pkey RENAME TO accounts_user_pkey")
                            cursor.execute("ALTER INDEX IF EXISTS auth_user_email_key RENAME TO accounts_user_email_key")
                            cursor.execute("ALTER INDEX IF EXISTS auth_user_username_key RENAME TO accounts_user_username_key")
                        except Exception as seq_err:
                            self.stdout.write(self.style.WARNING(f"Aviso al renombrar secuencias/índices: {seq_err}"))

                # Renombrar tablas de relaciones de grupos y permisos
                if 'auth_user_groups' in tables and 'accounts_user_groups' not in tables:
                    self.stdout.write(self.style.WARNING("Renombrando auth_user_groups a accounts_user_groups..."))
                    cursor.execute("ALTER TABLE auth_user_groups RENAME TO accounts_user_groups")
                if 'auth_user_user_permissions' in tables and 'accounts_user_user_permissions' not in tables:
                    self.stdout.write(self.style.WARNING("Renombrando auth_user_user_permissions a accounts_user_user_permissions..."))
                    cursor.execute("ALTER TABLE auth_user_user_permissions RENAME TO accounts_user_user_permissions")

                # Volver a leer las tablas para comprobar el perfil
                tables = connection.introspection.table_names(cursor)
                if 'accounts_userprofile' not in tables:
                    self.stdout.write(self.style.WARNING("Creando tabla accounts_userprofile para compatibilidad con 0001_initial..."))
                    is_postgres = 'postgresql' in connection.settings_dict['ENGINE'] or 'postgis' in connection.settings_dict['ENGINE']
                    if is_postgres:
                        cursor.execute("""
                            CREATE TABLE accounts_userprofile (
                                id SERIAL PRIMARY KEY,
                                plan VARCHAR(20) NOT NULL DEFAULT 'free',
                                plan_active_since DATE,
                                bio TEXT NOT NULL DEFAULT '',
                                profession VARCHAR(120) NOT NULL DEFAULT '',
                                avatar VARCHAR(100),
                                created_at TIMESTAMP WITH TIME ZONE,
                                user_id INTEGER NOT NULL UNIQUE REFERENCES accounts_user(id) DEFERRABLE INITIALLY DEFERRED
                            );
                        """)
                    else:
                        cursor.execute("""
                            CREATE TABLE accounts_userprofile (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                plan VARCHAR(20) NOT NULL DEFAULT 'free',
                                plan_active_since DATE,
                                bio TEXT NOT NULL DEFAULT '',
                                profession VARCHAR(120) NOT NULL DEFAULT '',
                                avatar VARCHAR(100),
                                created_at DATETIME,
                                user_id INTEGER NOT NULL UNIQUE REFERENCES accounts_user(id)
                            );
                        """)
                    self.stdout.write(self.style.SUCCESS("Tabla accounts_userprofile creada."))

            # 2. Si no hay tabla de usuarios en absoluto (instalación limpia), reseteamos esquema si no es sqlite
            elif 'accounts_user' not in tables:
                is_sqlite = 'sqlite' in connection.settings_dict['ENGINE']
                if not is_sqlite:
                    self.stdout.write(self.style.WARNING(
                        'prepare_db: accounts_user/auth_user ausentes — reseteando schema public para migrate limpio'
                    ))
                    cursor.execute("DROP SCHEMA public CASCADE")
                    cursor.execute("CREATE SCHEMA public")
                    cursor.execute("GRANT ALL ON SCHEMA public TO public")
                    self.stdout.write(self.style.SUCCESS('prepare_db: schema reseteado'))
                else:
                    self.stdout.write(self.style.SUCCESS('prepare_db: SQLite detectado sin tablas. Migrate correrá limpio.'))

            # 3. Asegurar que las migraciones clave estén registradas en django_migrations para consistencia
            # Volver a leer tablas de nuevo por si se recreó el esquema
            tables = connection.introspection.table_names(cursor)
            if 'django_migrations' in tables:
                from django.utils import timezone
                now = timezone.now()
                
                auth_migrations = [
                    '0001_initial', '0002_alter_permission_name_max_length', '0003_alter_user_email_max_length',
                    '0004_alter_user_username_opts', '0005_alter_user_last_login_null', '0006_require_contenttypes_0002',
                    '0007_alter_validators_add_error_messages', '0008_alter_user_username_max_length',
                    '0009_alter_user_last_name_max_length', '0010_alter_group_name_max_length',
                    '0011_update_proxy_permissions', '0012_alter_user_first_name_max_length',
                ]
                admin_migrations = [
                    '0001_initial', '0002_logentry_remove_auto_add', '0003_logentry_add_action_flag_choices',
                ]
                
                def restore_migrations(app_name, migration_list):
                    for name in migration_list:
                        cursor.execute("SELECT id FROM django_migrations WHERE app = %s AND name = %s", [app_name, name])
                        if not cursor.fetchone():
                            self.stdout.write(self.style.WARNING(f"Restaurando registro de migración: {app_name}.{name}"))
                            cursor.execute(
                                "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, %s)",
                                [app_name, name, now]
                            )

                restore_migrations('auth', auth_migrations)
                restore_migrations('admin', admin_migrations)
                restore_migrations('accounts', ['0001_initial'])
                self.stdout.write(self.style.SUCCESS("prepare_db: Registros de migración de auth, admin y accounts asegurados."))

            self.stdout.write(self.style.SUCCESS('prepare_db: BD OK'))
