from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("list/", views.users_list_view, name="list"),
    path("edit-profile/", views.edit_profile_view, name="edit_profile"),
    path("change-password/", views.change_password_view, name="change_password"),
    path("skills/", views.user_skills_suggest_view, name="skills_suggest"),
    path("<int:user_id>/", views.profile_view, name="profile"),
    path("<int:user_id>/skills/add/", views.user_skill_add_view, name="skill_add"),
    path("<int:user_id>/skills/<int:skill_id>/remove/", views.user_skill_remove_view, name="skill_remove"),
]
