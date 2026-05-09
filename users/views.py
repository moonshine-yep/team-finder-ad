from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import (
    LoginForm,
    RegisterForm,
    UserEditForm,
    UserPasswordChangeForm,
    parse_json_body,
)
from .models import Skill, User


@require_http_methods(["GET", "POST"])
def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("/projects/list/")
    return render(request, "users/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    form = LoginForm(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("/projects/list/")
    return render(request, "users/login.html", {"form": form})


@require_GET
def logout_view(request):
    logout(request)
    return redirect("/projects/list/")


@require_GET
def users_list_view(request):
    participants = User.objects.all().prefetch_related("skills")
    skill = request.GET.get("skill", "").strip()
    if skill:
        participants = participants.filter(skills__name=skill)
    participants = participants.order_by("-id").distinct()
    all_skills = Skill.objects.order_by("name")
    return render(
        request,
        "users/participants.html",
        {
            "participants": participants,
            "all_skills": all_skills,
            "active_skill": skill,
            "active_filter": request.GET.get("filter", "").strip(),
        },
    )


@require_GET
def profile_view(request, user_id):
    profile = get_object_or_404(User.objects.prefetch_related("owned_projects", "skills"), pk=user_id)
    return render(request, "users/user-details.html", {"user": profile})


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile_view(request):
    form = UserEditForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(f"/users/{request.user.id}/")
    return render(request, "users/edit_profile.html", {"form": form, "from": form})


@login_required
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    form = UserPasswordChangeForm(user=request.user, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect(f"/users/{request.user.id}/")
    return render(request, "users/change_password.html", {"form": form, "from": form})


@login_required
@require_GET
def user_skills_suggest_view(request):
    q = request.GET.get("q", "").strip()
    skills = Skill.objects.filter(name__istartswith=q).order_by("name")[:10] if q else Skill.objects.none()
    return JsonResponse(list(skills.values("id", "name")), safe=False)


@login_required
@require_POST
def user_skill_add_view(request, user_id):
    if request.user.id != user_id:
        return JsonResponse({"status": "error"}, status=403)
    payload = parse_json_body(request)
    skill_id = payload.get("skill_id")
    name = (payload.get("name") or "").strip()
    if not skill_id and not name:
        return HttpResponseBadRequest("skill_id or name required")
    created = False
    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    else:
        skill, created = Skill.objects.get_or_create(name=name)
    already = request.user.skills.filter(pk=skill.pk).exists()
    if not already:
        request.user.skills.add(skill)
    return JsonResponse(
        {
            "skill_id": skill.id,
            "id": skill.id,
            "name": skill.name,
            "created": created,
            "added": not already,
        }
    )


@login_required
@require_POST
def user_skill_remove_view(request, user_id, skill_id):
    if request.user.id != user_id:
        return JsonResponse({"status": "error"}, status=403)
    skill = get_object_or_404(Skill, pk=skill_id)
    request.user.skills.remove(skill)
    return JsonResponse({"status": "ok"})
