import io
import random
import re
from urllib.parse import urlparse

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from django.db import models
from PIL import Image, ImageDraw, ImageFont

from .managers import UserManager

PHONE_REGEX = re.compile(r"^(8\d{10}|\+7\d{10})$")


class Skill(models.Model):
    name = models.CharField(max_length=124, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


def avatar_upload_path(instance, filename):
    return f"avatars/user_{instance.pk or 'new'}/{filename}"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)
    avatar = models.ImageField(upload_to=avatar_upload_path, blank=True)
    phone = models.CharField(
        max_length=12,
        blank=True,
        validators=[RegexValidator(regex=PHONE_REGEX.pattern)],
    )
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=256, blank=True)
    skills = models.ManyToManyField(Skill, related_name="users", blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    objects = UserManager()

    class Meta:
        ordering = ("-id",)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.avatar:
            self.avatar.save(f"avatar_{self.pk}.png", self._generate_avatar(), save=True)

    @property
    def normalized_phone(self):
        if not self.phone:
            return ""
        return "+7" + self.phone[1:] if self.phone.startswith("8") else self.phone

    @staticmethod
    def is_github_url(value):
        if not value:
            return True
        host = urlparse(value).netloc.lower()
        return host in {"github.com", "www.github.com"}

    def _generate_avatar(self):
        size = (256, 256)
        backgrounds = ["#5E81AC", "#6C8F84", "#7A6F9B", "#8A7D5C", "#4D7EA8"]
        img = Image.new("RGB", size, color=random.choice(backgrounds))
        draw = ImageDraw.Draw(img)
        letter = (self.name[:1] or "U").upper()
        font_size = 120
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), letter, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (size[0] - text_w) / 2
        y = (size[1] - text_h) / 2 - 8
        draw.text((x, y), letter, fill="white", font=font)
        stream = io.BytesIO()
        img.save(stream, format="PNG")
        return ContentFile(stream.getvalue())
