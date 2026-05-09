from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("list/", views.project_list_view, name="list"),
    path("create-project/", views.project_create_view, name="create"),
    path("skills/", views.project_skills_suggest_view, name="skills_suggest"),
    path("<int:project_id>/", views.project_details_view, name="details"),
    path("<int:project_id>/edit/", views.project_edit_view, name="edit"),
    path("<int:project_id>/complete/", views.project_complete_view, name="complete"),
    path("<int:project_id>/toggle-participate/", views.project_toggle_participate_view, name="toggle_participate"),
    path("<int:project_id>/skills/add/", views.project_skill_add_view, name="skill_add"),
    path("<int:project_id>/skills/<int:skill_id>/remove/", views.project_skill_remove_view, name="skill_remove"),
]
