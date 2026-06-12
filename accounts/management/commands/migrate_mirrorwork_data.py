import json
import os
import sqlite3
from django.core.management.base import BaseCommand
from django.db import transaction
import dj_database_url
import psycopg2


class Command(BaseCommand):
    help = 'Migra usuarios, perfiles, fractones, tests y sesiones del Espejo desde una base de datos de mirrorwork antigua'

    def add_arguments(self, parser):
        parser.add_argument('old_db_url', type=str, nargs='?', default=None, help='DATABASE_URL o ruta al archivo sqlite de la BD vieja')

    def handle(self, *args, **options):
        old_db_url = options['old_db_url'] or os.getenv('OLD_DATABASE_URL')
        if not old_db_url:
            self.stdout.write("Variable de entorno 'OLD_DATABASE_URL' no configurada. Omitiendo migración de datos.")
            return
        
        # Conectar a la base de datos vieja
        if old_db_url.startswith('postgres://') or old_db_url.startswith('postgresql://'):
            self.stdout.write(f"Conectando a base de datos PostgreSQL vieja...")
            conn = psycopg2.connect(old_db_url)
        else:
            self.stdout.write(f"Conectando a base de datos SQLite vieja: {old_db_url}...")
            conn = sqlite3.connect(old_db_url)

        try:
            self.stdout.write("Obteniendo datos de la base de datos vieja...")
            
            # Helper para consultar una tabla de forma segura
            def get_data(table):
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM {table}")
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"No se pudo leer la tabla {table}: {e}"))
                    return []

            users = get_data('accounts_user')
            profiles = get_data('accounts_userprofile')
            balances = get_data('tokens_tokenbalance')
            transactions = get_data('tokens_tokentransaction')
            sessions = get_data('mirror_conflictsession')
            memorias = get_data('mirror_espejomemoria')
            results = get_data('psychometrics_testresult')
            posts = get_data('community_post')
            likes = get_data('community_postlike')
            comments = get_data('community_postcomment')

            self.stdout.write(f"Encontrados: {len(users)} usuarios, {len(sessions)} sesiones, {len(memorias)} memorias, {len(results)} resultados.")

            # Importar con transacción atómica
            with transaction.atomic():
                from django.contrib.auth import get_user_model
                User = get_user_model()
                from accounts.models import UserProfile
                from tokens.models import TokenBalance, TokenTransaction
                from mirror.models import ConflictSession, EspejoMemoria
                from psychometrics.models import TestResult
                from community.models import Post, PostLike, PostComment

                # 1. Usuarios
                for u in users:
                    if User.objects.filter(id=u['id']).exists():
                        self.stdout.write(f"Usuario ID={u['id']} ({u['email']}) ya existe en destino, omitiendo.")
                        continue
                    if User.objects.filter(email=u['email']).exists():
                        self.stdout.write(f"Usuario email={u['email']} ya existe en destino, omitiendo.")
                        continue
                    
                    # Campos booleanos
                    u['is_superuser'] = bool(u.get('is_superuser'))
                    u['is_staff'] = bool(u.get('is_staff'))
                    u['is_active'] = bool(u.get('is_active'))
                    
                    obj = User(**u)
                    obj.save(force_insert=True)
                    self.stdout.write(f"  ✓ Importado usuario: {u['email']}")

                # 2. Perfiles de usuario
                for p in profiles:
                    if UserProfile.objects.filter(id=p['id']).exists():
                        continue
                    if not User.objects.filter(id=p['user_id']).exists():
                        continue
                    
                    p['profile_public'] = bool(p.get('profile_public'))
                    if isinstance(p.get('social_links'), str):
                        p['social_links'] = json.loads(p['social_links'])
                    if isinstance(p.get('onboarding_nucleo'), str):
                        p['onboarding_nucleo'] = json.loads(p['onboarding_nucleo'])
                        
                    obj = UserProfile(**p)
                    obj.save(force_insert=True)

                # 3. Balances de Fractones
                for b in balances:
                    if TokenBalance.objects.filter(id=b['id']).exists():
                        continue
                    if not User.objects.filter(id=b['user_id']).exists():
                        continue
                    obj = TokenBalance(**b)
                    obj.save(force_insert=True)

                # 4. Transacciones
                for t in transactions:
                    if TokenTransaction.objects.filter(id=t['id']).exists():
                        continue
                    if not User.objects.filter(id=t['user_id']).exists():
                        continue
                    obj = TokenTransaction(**t)
                    obj.save(force_insert=True)

                # 5. Sesiones de Conflicto
                for s in sessions:
                    if ConflictSession.objects.filter(id=s['id']).exists():
                        continue
                    if s.get('user_id') and not User.objects.filter(id=s['user_id']).exists():
                        continue
                    
                    if isinstance(s.get('messages'), str):
                        s['messages'] = json.loads(s['messages'])
                        
                    obj = ConflictSession(**s)
                    obj.save(force_insert=True)
                    self.stdout.write(f"  ✓ Importada sesión del espejo: {s['title'] or s['id']}")

                # 6. Memorias del Espejo
                for m in memorias:
                    if EspejoMemoria.objects.filter(id=m['id']).exists():
                        continue
                    if not User.objects.filter(id=m['user_id']).exists():
                        continue
                    if m.get('sesion_origen_id') and not ConflictSession.objects.filter(id=m['sesion_origen_id']).exists():
                        m['sesion_origen_id'] = None
                        
                    m['activa'] = bool(m.get('activa'))
                    obj = EspejoMemoria(**m)
                    obj.save(force_insert=True)

                # 7. Resultados de Tests
                for r in results:
                    if TestResult.objects.filter(id=r['id']).exists():
                        continue
                    if not User.objects.filter(id=r['user_id']).exists():
                        continue
                    from psychometrics.models import Test
                    if not Test.objects.filter(id=r['test_id']).exists():
                        continue
                    
                    if isinstance(r.get('dimension_scores'), str):
                        r['dimension_scores'] = json.loads(r['dimension_scores'])
                    if isinstance(r.get('metadata'), str):
                        r['metadata'] = json.loads(r['metadata'])
                        
                    obj = TestResult(**r)
                    obj.save(force_insert=True)

                # 8. Posts de comunidad
                for po in posts:
                    if Post.objects.filter(id=po['id']).exists():
                        continue
                    if not User.objects.filter(id=po['author_id']).exists():
                        continue
                    po['is_free'] = bool(po.get('is_free', True))
                    obj = Post(**po)
                    obj.save(force_insert=True)

                # 9. Likes
                for l in likes:
                    if PostLike.objects.filter(id=l['id']).exists():
                        continue
                    if not User.objects.filter(id=l['user_id']).exists():
                        continue
                    if not Post.objects.filter(id=l['post_id']).exists():
                        continue
                    obj = PostLike(**l)
                    obj.save(force_insert=True)

                # 10. Comentarios
                for c_item in comments:
                    if PostComment.objects.filter(id=c_item['id']).exists():
                        continue
                    if not User.objects.filter(id=c_item['user_id']).exists():
                        continue
                    if not Post.objects.filter(id=c_item['post_id']).exists():
                        continue
                    obj = PostComment(**c_item)
                    obj.save(force_insert=True)

            self.stdout.write(self.style.SUCCESS("Migración finalizada con éxito."))

        finally:
            conn.close()
