from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        from tokens.models import TokenBalance
        TokenBalance.objects.create(
            user=instance,
            monthly=settings.TOKEN_PLANS['free']['monthly_fractones']
        )

        # Registrar al usuario en el CRM
        try:
            from crm.models import Subscriber, EmailList, Subscription
            subscriber, sub_created = Subscriber.objects.get_or_create(
                email=instance.email,
                defaults={'name': instance.first_name or instance.username.split('@')[0]}
            )
            email_list, list_created = EmailList.objects.get_or_create(
                slug='comunidad',
                defaults={
                    'name': 'Comunidad Endonautas',
                    'description': 'Usuarios registrados en la plataforma'
                }
            )
            Subscription.objects.get_or_create(
                subscriber=subscriber,
                email_list=email_list,
                defaults={'source': 'registro-plataforma'}
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error registrando usuario {instance.email} en CRM: {e}")
