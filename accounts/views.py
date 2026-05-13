from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django import forms
from .models import User


class RegisterForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico')
    first_name = forms.CharField(label='Nombre', max_length=60)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput, min_length=8)
    password_confirm = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password_confirm')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=form.cleaned_data['first_name'],
            password=form.cleaned_data['password'],
        )
        login(request, user)
        return redirect('onboarding_mapa')
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    error = None
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['email'].lower(),
            password=form.cleaned_data['password'],
        )
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        error = 'Correo o contraseña incorrectos.'
    return render(request, 'accounts/login.html', {'form': form, 'error': error})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    try:
        if not request.user.profile.map_aesthetic:
            return redirect('onboarding_mapa')
    except Exception:
        return redirect('onboarding_mapa')

    from psychometrics.models import TestResult, Test
    from tokens.models import TokenBalance
    recent_results = TestResult.objects.filter(user=request.user).select_related('test')[:5]
    try:
        token_balance = request.user.token_balance
    except Exception:
        token_balance = None
    total_tests = Test.objects.filter(active=True).count()
    completed_tests = (
        TestResult.objects.filter(user=request.user).values('test').distinct().count()
    )
    map_pct = round(completed_tests / total_tests * 100) if total_tests else 0
    return render(request, 'dashboard.html', {
        'recent_results': recent_results,
        'token_balance': token_balance,
        'map_aesthetic': request.user.profile.map_aesthetic,
        'map_pct': map_pct,
        'completed_tests': completed_tests,
        'total_tests': total_tests,
    })


_VALID_AESTHETICS = {'cosmos', 'mandala', 'archipielago', 'arbol'}

@login_required
def onboarding_mapa(request):
    try:
        profile = request.user.profile
    except Exception:
        from .models import UserProfile
        profile = UserProfile.objects.create(user=request.user)

    if profile.map_aesthetic:
        return redirect('dashboard')

    if request.method == 'POST':
        choice = request.POST.get('map_aesthetic', '')
        if choice in _VALID_AESTHETICS:
            profile.map_aesthetic = choice
            profile.save(update_fields=['map_aesthetic'])
            return redirect('dashboard')

    return render(request, 'accounts/onboarding_mapa.html')


def bienvenido(request):
    return render(request, 'bienvenido.html')


_DIMENSION_LABELS = {
    'identidad':      'Identidad',
    'emociones':      'Emociones',
    'sombra':         'Sombra',
    'cuerpo':         'Cuerpo',
    'mente':          'Mente',
    'proposito':      'Propósito',
    'espiritualidad': 'Espiritualidad',
    'vinculos':       'Vínculos',
    'creatividad':    'Creatividad',
    'comunidad':      'Comunidad',
    'suenos':         'Sueños',
    'abundancia':     'Abundancia',
}


@login_required
def mapa_interior(request):
    import json
    try:
        profile = request.user.profile
    except Exception:
        return redirect('onboarding_mapa')
    if not profile.map_aesthetic:
        return redirect('onboarding_mapa')

    from psychometrics.models import Test, TestResult

    dim_data = {}
    for dim, label in _DIMENSION_LABELS.items():
        total = Test.objects.filter(dimension=dim, active=True).count()
        completed = (
            TestResult.objects.filter(user=request.user, test__dimension=dim)
            .values('test').distinct().count()
        )
        pct = round(completed / total * 100) if total else 0
        dim_data[dim] = {'label': label, 'total': total, 'completed': completed, 'pct': pct}

    total_tests = sum(d['total'] for d in dim_data.values())
    completed_tests = sum(d['completed'] for d in dim_data.values())
    total_pct = round(completed_tests / total_tests * 100) if total_tests else 0

    return render(request, 'accounts/mapa_interior.html', {
        'dim_data': dim_data,
        'dim_data_json': json.dumps(dim_data),
        'aesthetic': profile.map_aesthetic,
        'total_pct': total_pct,
        'completed_tests': completed_tests,
        'total_tests': total_tests,
    })
