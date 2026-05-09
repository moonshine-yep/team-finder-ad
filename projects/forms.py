from urllib.parse import urlparse

from django import forms

from .models import Project


def github_url_valid(url):
    if not url:
        return True
    host = urlparse(url).netloc.lower()
    return host in {"github.com", "www.github.com"}


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        labels = {
            "name": "Название",
            "description": "Описание проекта",
            "github_url": "Ссылка на GitHub",
            "status": "Статус",
        }

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url", "").strip()
        if url and not github_url_valid(url):
            raise forms.ValidationError("Укажите ссылку именно на github.com")
        return url
