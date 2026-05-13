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
        return redirect('dashboard')
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
    from psychometrics.models import TestResult
    from tokens.models import TokenBalance
    recent_results = TestResult.objects.filter(user=request.user).select_related('test')[:5]
    try:
        token_balance = request.user.token_balance
    except Exception:
        token_balance = None
    return render(request, 'dashboard.html', {
        'recent_results': recent_results,
        'token_balance': token_balance,
    })


def bienvenido(request):
    return render(request, 'bienvenido.html')
