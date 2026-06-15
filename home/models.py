from django.db import models
from wagtail.models import Page
from wagtail.api import APIField
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail import blocks
import json

class LeadMagnetBlock(blocks.StructBlock):
    MAGNET_CHOICES = [
        ('mascara', 'Test de Máscaras'),
        ('hacks', '3 Hacks de Endonáutica'),
        ('viaje', 'Viaje Interior'),
        ('endonautica', 'Libro Endonáutica'),
    ]
    
    magnet_type = blocks.ChoiceBlock(choices=MAGNET_CHOICES, required=True, label="Tipo de Magnet")
    headline = blocks.CharBlock(required=True, label="Titular/Frase principal")
    cta_text = blocks.CharBlock(required=True, default="Acceder →", label="Texto del botón")
    brevo_list_id = blocks.IntegerBlock(required=False, label="ID Lista Brevo", help_text="Para magnets gratuitos")
    hotmart_url = blocks.URLBlock(required=False, label="URL Hotmart", help_text="Para magnets de pago")
    
    class Meta:
        icon = 'form'
        label = 'Tarjeta de Lead Magnet (Bento Grid)'


class HomePage(Page):
    tagline = models.CharField(max_length=200, blank=True)
    intro = RichTextField(blank=True)
    cta_app_text = models.CharField(max_length=80, default='Comenzar el viaje')
    cta_app_url = models.URLField(default='https://app.endonautas.cl')
    cta_ebook_text = models.CharField(max_length=80, default='Descargar Endonautica')
    cta_ebook_url = models.URLField(default='https://ebook.endonautas.cl')
    
    lead_magnets = StreamField([
        ('lead_magnet', LeadMagnetBlock())
    ], blank=True, use_json_field=True, verbose_name="Bento Grid de Magnets")

    content_panels = Page.content_panels + [
        FieldPanel('tagline'),
        FieldPanel('intro'),
        FieldPanel('cta_app_text'),
        FieldPanel('cta_app_url'),
        FieldPanel('cta_ebook_text'),
        FieldPanel('cta_ebook_url'),
        FieldPanel('lead_magnets'),
    ]

    api_fields = [
        APIField('tagline'),
        APIField('intro'),
        APIField('cta_app_text'),
        APIField('cta_app_url'),
        APIField('cta_ebook_text'),
        APIField('cta_ebook_url'),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['onboarding_source'] = request.GET.get('onboarding', '')
        if request.user.is_authenticated:
            from psychometrics.models import Test, TestResult
            from tokens.models import TokenBalance, TokenTransaction
            from mirror.models import ConflictSession
            from community.models import SharedInsight, Follow
            from community.views import _ranked, _get_facilitador
            from accounts.models import UserProfile

            # Ensure profile exists
            try:
                profile = request.user.profile
            except Exception:
                profile = UserProfile.objects.create(user=request.user)

            try:
                token_balance = request.user.token_balance.balance
            except Exception:
                token_balance = 0

            total_tests = Test.objects.filter(active=True).count()
            completed_tests = TestResult.objects.filter(user=request.user).values('test').distinct().count()
            map_pct = round(completed_tests / total_tests * 100) if total_tests else 0

            mirror_sessions = ConflictSession.objects.filter(user=request.user).order_by("-updated_at")[:10]

            # Query community feed insights
            following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            facilitador = _get_facilitador(request.user)
            author_ids = set(following_ids)
            if facilitador:
                author_ids.add(facilitador.pk)
            author_ids.add(request.user.pk)

            qs = SharedInsight.objects.filter(user_id__in=author_ids, visibility=SharedInsight.VISIBILITY_PUBLIC)
            insights, facilitador = _ranked(qs, request.user)
            
            # Build a set of completed test IDs for the template
            completed_test_ids = set(
                TestResult.objects.filter(user=request.user).values_list('test_id', flat=True).distinct()
            )
            # All active tests ordered for the map/interior page
            tests_qs = Test.objects.filter(active=True).order_by('order', 'name')

            context.update({
                'token_balance_val': token_balance,
                'completed_tests_val': completed_tests,
                'total_tests_val': total_tests,
                'map_pct_val': map_pct,
                'mirror_sessions': mirror_sessions,
                'feed_insights': insights[:40],
                'facilitador': facilitador,
                'viewer_pk': request.user.pk,
                'user_plan_val': profile.get_plan_display(),
                'user_avatar_url': profile.avatar.url if profile.avatar else '',
                'tests': tests_qs,
                'completed_test_ids': completed_test_ids,
            })
        else:
            context.update({
                'token_balance_val': 450,
                'completed_tests_val': 4,
                'total_tests_val': 12,
                'map_pct_val': 33,
                'mirror_sessions': [],
                'feed_insights': [],
                'facilitador': None,
                'viewer_pk': None,
                'user_plan_val': 'Mi Cuenta',
                'tests': [],
                'completed_test_ids': set(),
            })
        return context

    def get_structured_data_json(self):
        data = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "Endonautas",
            "url": "https://endonautas.cl",
            "description": self.tagline,
            "potentialAction": {
                "@type": "SearchAction",
                "target": "https://endonautas.cl/blog/?q={search_term_string}",
                "query-input": "required name=search_term_string"
            }
        }
        return json.dumps(data, ensure_ascii=False)

    class Meta:
        verbose_name = 'Página de Inicio'

class SimplePage(Page):
    body = RichTextField(blank=True)
    cta_text = models.CharField(max_length=80, blank=True)
    cta_url = models.URLField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('body'),
        FieldPanel('cta_text'),
        FieldPanel('cta_url'),
    ]

    class Meta:
        verbose_name = 'Página Simple'
