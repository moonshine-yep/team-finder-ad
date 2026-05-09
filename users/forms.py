import json
import re
from urllib.parse import urlparse

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm

from .models import User

PHONE_PATTERN = re.compile(r"^(8\d{10}|\+7\d{10})$")


def normalize_phone(phone):
    if not phone:
        return ""
    return "+7" + phone[1:] if phone.startswith("8") else phone


def github_url_valid(url):
    if not url:
        return True
    host = urlparse(url).netloc.lower()
    return host in {"github.com", "www.github.com"}


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            self.user = authenticate(self.request, email=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Неверный имейл или пароль")
        return cleaned

    def get_user(self):
        return self.user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            return ""
        if not PHONE_PATTERN.match(phone):
            raise forms.ValidationError("Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX")
        normalized = normalize_phone(phone)
        exists = User.objects.exclude(pk=self.instance.pk).filter(phone__in=[phone, normalized]).exists()
        if exists:
            raise forms.ValidationError("Этот номер телефона уже используется")
        return normalized

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url", "").strip()
        if url and not github_url_valid(url):
            raise forms.ValidationError("Укажите ссылку именно на github.com")
        return url


class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput, label="Текущий пароль")
    new_password1 = forms.CharField(widget=forms.PasswordInput, label="Новый пароль")
    new_password2 = forms.CharField(widget=forms.PasswordInput, label="Подтвердите новый пароль")


def parse_json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
