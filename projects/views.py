from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from users.forms import parse_json_body
from users.models import Skill

from .forms import ProjectForm
from .models import Project


@require_GET
def root_redirect_view(request):
    return redirect("/projects/list/")


@require_GET
def project_list_view(request):
    projects = (
        Project.objects.select_related("owner")
        .prefetch_related("participants", "skills")
        .order_by("-created_at")
    )
    skill = request.GET.get("skill", "").strip()
    if skill:
        projects = projects.filter(skills__name=skill).distinct()
    all_skills = Skill.objects.order_by("name")
    return render(
        request,
        "projects/project_list.html",
        {"projects": projects, "all_skills": all_skills, "active_skill": skill},
    )


@require_GET
def project_details_view(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants", "skills"),
        pk=project_id,
    )
    return render(request, "projects/project-details.html", {"project": project})


@login_required
@require_POST
def project_complete_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id or project.status != Project.STATUS_OPEN:
        return JsonResponse({"status": "error"}, status=400)
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": project.status})


@login_required
@require_POST
def project_toggle_participate_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.participants.filter(pk=request.user.id).exists():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True
    return JsonResponse({"status": "ok", "participant": participant})


@login_required
@require_http_methods(["GET", "POST"])
def project_create_view(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        project.participants.add(request.user)
        return redirect(f"/projects/{project.id}/")
    return render(request, "projects/create-project.html", {"form": form, "is_edit": False})


@login_required
@require_http_methods(["GET", "POST"])
def project_edit_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id:
        return HttpResponseForbidden()
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(f"/projects/{project.id}/")
    return render(request, "projects/create-project.html", {"form": form, "is_edit": True})


@login_required
@require_GET
def project_skills_suggest_view(request):
    q = request.GET.get("q", "").strip()
    skills = Skill.objects.filter(name__istartswith=q).order_by("name")[:10] if q else Skill.objects.none()
    return JsonResponse(list(skills.values("id", "name")), safe=False)


@login_required
@require_POST
def project_skill_add_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id:
        return JsonResponse({"status": "error"}, status=403)
    payload = parse_json_body(request)
    skill_id = payload.get("skill_id")
    name = (payload.get("name") or "").strip()
    created = False
    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    elif name:
        skill, created = Skill.objects.get_or_create(name=name)
    else:
        return JsonResponse({"status": "error"}, status=400)
    already = project.skills.filter(pk=skill.pk).exists()
    if not already:
        project.skills.add(skill)
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
def project_skill_remove_view(request, project_id, skill_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id:
        return JsonResponse({"status": "error"}, status=403)
    skill = get_object_or_404(Skill, pk=skill_id)
    project.skills.remove(skill)
    return JsonResponse({"status": "ok"})
