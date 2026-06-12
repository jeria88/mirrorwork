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
        # Disconnect signals to prevent side effects and unique constraint violations during data migration
        from django.db.models.signals import post_save
        from accounts.signals import create_user_profile
        from tokens.signals import on_test_completed, on_session_archived
        from django.contrib.auth import get_user_model
        User = get_user_model()
        from psychometrics.models import TestResult
        from mirror.models import ConflictSession

        post_save.disconnect(create_user_profile, sender=User)
        post_save.disconnect(on_test_completed, sender=TestResult)
        post_save.disconnect(on_session_archived, sender=ConflictSession)
        self.stdout.write("Señales de Django desconectadas temporalmente para la migración.")

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
            posts = get_data('community_sharedinsight') or get_data('community_post')
            likes = get_data('community_reaction') or get_data('community_postlike')
            comments = get_data('community_comment') or get_data('community_postcomment')

            self.stdout.write(f"Encontrados: {len(users)} usuarios, {len(sessions)} sesiones, {len(memorias)} memorias, {len(results)} resultados.")

            # Importar con transacción atómica
            with transaction.atomic():
                from django.contrib.auth import get_user_model
                User = get_user_model()
                from accounts.models import UserProfile
                from tokens.models import TokenBalance, TokenTransaction
                from mirror.models import ConflictSession, EspejoMemoria
                from psychometrics.models import TestResult
                from community.models import SharedInsight, Reaction, Comment

                # Helper to filter keys matching active Django model fields
                def clean_record(model, data):
                    valid_keys = {f.name for f in model._meta.get_fields()}
                    clean_data = {}
                    for k, v in data.items():
                        if k in valid_keys:
                            clean_data[k] = v
                        elif k.endswith('_id') and k[:-3] in valid_keys:
                            clean_data[k] = v
                    return clean_data

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
                    
                    clean_u = clean_record(User, u)
                    obj = User(**clean_u)
                    obj.save(force_insert=True)
                    self.stdout.write(f"  ✓ Importado usuario: {u['email']}")

                # 2. Perfiles de usuario
                for p in profiles:
                    if not User.objects.filter(id=p['user_id']).exists():
                        continue
                    
                    p['profile_public'] = bool(p.get('profile_public'))
                    if isinstance(p.get('social_links'), str):
                        p['social_links'] = json.loads(p['social_links'])
                    if isinstance(p.get('onboarding_nucleo'), str):
                        p['onboarding_nucleo'] = json.loads(p['onboarding_nucleo'])
                        
                    clean_p = clean_record(UserProfile, p)
                    
                    # Al ser OneToOne, si ya existe el perfil del usuario (creado por signals), lo actualizamos
                    existing_p = UserProfile.objects.filter(user_id=p['user_id']).first()
                    if existing_p:
                        for key, val in clean_p.items():
                            if key != 'id':
                                setattr(existing_p, key, val)
                        existing_p.save()
                    else:
                        obj = UserProfile(**clean_p)
                        obj.save(force_insert=True)

                # 3. Balances de Fractones
                for b in balances:
                    if not User.objects.filter(id=b['user_id']).exists():
                        continue
                    
                    clean_b = clean_record(TokenBalance, b)
                    
                    # Al ser OneToOne, si ya existe el balance (creado por signals), lo actualizamos
                    existing_b = TokenBalance.objects.filter(user_id=b['user_id']).first()
                    if existing_b:
                        for key, val in clean_b.items():
                            if key != 'id':
                                setattr(existing_b, key, val)
                        existing_b.save()
                    else:
                        obj = TokenBalance(**clean_b)
                        obj.save(force_insert=True)

                # 4. Transacciones
                for t in transactions:
                    if TokenTransaction.objects.filter(id=t['id']).exists():
                        continue
                    if not User.objects.filter(id=t['user_id']).exists():
                        continue
                    clean_t = clean_record(TokenTransaction, t)
                    obj = TokenTransaction(**clean_t)
                    obj.save(force_insert=True)

                # 5. Sesiones de Conflicto
                for s in sessions:
                    if ConflictSession.objects.filter(id=s['id']).exists():
                        continue
                    if s.get('user_id') and not User.objects.filter(id=s['user_id']).exists():
                        continue
                    
                    if isinstance(s.get('messages'), str):
                        s['messages'] = json.loads(s['messages'])
                        
                    clean_s = clean_record(ConflictSession, s)
                    obj = ConflictSession(**clean_s)
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
                    clean_m = clean_record(EspejoMemoria, m)
                    obj = EspejoMemoria(**clean_m)
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
                        
                    clean_r = clean_record(TestResult, r)
                    obj = TestResult(**clean_r)
                    obj.save(force_insert=True)

                # 8. Posts de comunidad (SharedInsight)
                for po in posts:
                    if SharedInsight.objects.filter(id=po['id']).exists():
                        continue
                    user_id = po.get('user_id') or po.get('author_id')
                    if not user_id or not User.objects.filter(id=user_id).exists():
                        continue
                    
                    # Map legacy fields if necessary
                    if 'author_id' in po and 'user_id' not in po:
                        po['user_id'] = po.pop('author_id')
                    if 'is_free' in po:
                        po.pop('is_free')
                        
                    clean_po = clean_record(SharedInsight, po)
                    obj = SharedInsight(**clean_po)
                    obj.save(force_insert=True)

                # 9. Likes (Reaction)
                for l in likes:
                    if Reaction.objects.filter(id=l['id']).exists():
                        continue
                    if not User.objects.filter(id=l.get('user_id')).exists():
                        continue
                    if 'post_id' in l and 'insight_id' not in l:
                        l['insight_id'] = l.pop('post_id')
                    if 'type' not in l:
                        l['type'] = 'resonó'
                        
                    clean_l = clean_record(Reaction, l)
                    obj = Reaction(**clean_l)
                    obj.save(force_insert=True)

                # 10. Comentarios (Comment)
                for c_item in comments:
                    if Comment.objects.filter(id=c_item['id']).exists():
                        continue
                    if not User.objects.filter(id=c_item.get('user_id')).exists():
                        continue
                    if 'post_id' in c_item and 'insight_id' not in c_item:
                        c_item['insight_id'] = c_item.pop('post_id')
                        
                    clean_c = clean_record(Comment, c_item)
                    obj = Comment(**clean_c)
                    obj.save(force_insert=True)

            self.stdout.write(self.style.SUCCESS("Migración finalizada con éxito."))

        finally:
            conn.close()
