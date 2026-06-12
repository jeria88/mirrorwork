from django.core.management.base import BaseCommand
from accounts.models import User, UserProfile
from tokens.models import TokenBalance, TokenTransaction


class Command(BaseCommand):
    help = 'Crea usuario admin de testing si no existe'

    def handle(self, *args, **options):
        email = 'admin@mirrorwork.app'
        password = 'Mirror2026!'

        # Look up by email first, then by username to avoid UniqueViolation
        u = User.objects.filter(email=email).first()
        if not u:
            u = User.objects.filter(username='admin').first()

        created = False
        if u is None:
            u = User(email=email, username='admin', is_staff=True, is_superuser=True)
            u.set_password(password)
            u.save()
            created = True
            self.stdout.write(self.style.SUCCESS(f'Admin creado: {email}'))
        else:
            # Ensure admin attributes are correct
            changed = False
            if not u.is_staff:
                u.is_staff = True
                changed = True
            if not u.is_superuser:
                u.is_superuser = True
                changed = True
            if u.email != email:
                u.email = email
                changed = True
            if u.username != 'admin':
                u.username = 'admin'
                changed = True
            if changed:
                u.save()
            self.stdout.write(f'Admin ya existe: {u.email} (id={u.id})')

        profile, _ = UserProfile.objects.get_or_create(user=u)
        if profile.plan != 'empresa':
            profile.plan = 'empresa'
            profile.save()

        balance, _ = TokenBalance.objects.get_or_create(user=u)
        if balance.balance < 999999:
            balance.permanent = 999999
            balance.monthly = 0
            balance.save()
            TokenTransaction.objects.create(user=u, amount=999999, reason='Admin test — ilimitado')

