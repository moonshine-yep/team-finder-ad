from django.db import models

from users.models import Skill, User


class Project(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = ((STATUS_OPEN, "Open"), (STATUS_CLOSED, "Closed"))

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, related_name="owned_projects", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    github_url = models.URLField(blank=True)
    status = models.CharField(max_length=6, choices=STATUS_CHOICES, default=STATUS_OPEN)
    participants = models.ManyToManyField(User, related_name="participated_projects", blank=True)
    skills = models.ManyToManyField(Skill, related_name="projects", blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name
