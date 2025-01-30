from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json
from .models import Project, Task

@login_required
def home(request):
    return render(request, 'main/home.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})

@login_required
def projects(request):
    if request.method == 'POST':
        if 'project_id' in request.POST:  # Adding new task
            project = get_object_or_404(Project, id=request.POST['project_id'])
            if not project.can_user_edit(request.user):
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            Task.objects.create(
                project=project,
                title=request.POST['title'],
                description=request.POST['description']
            )
            return redirect('projects')
        else:  # Adding new project
            project = Project.objects.create(
                owner=request.user,
                title=request.POST['title'],
                description=request.POST['description'],
                is_public=True
            )
            return redirect('projects')
    
    # Get all accessible projects
    accessible_projects = Project.objects.filter(
        Q(is_public=True) |
        Q(owner=request.user) |
        Q(participants=request.user)
    ).distinct()
    
    return render(request, 'main/projects.html', {'projects': accessible_projects})

@login_required
@require_http_methods(['POST'])
def update_task_status(request):
    data = json.loads(request.body)
    task_id = data.get('task_id')
    new_status = data.get('new_status')
    
    try:
        task = Task.objects.get(id=task_id)
        if not task.project.can_user_edit(request.user):
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        task.status = new_status
        task.save()
        return JsonResponse({'success': True})
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)

@login_required
@require_http_methods(['POST'])
def update_task(request):
    data = json.loads(request.body)
    task_id = data.get('task_id')
    title = data.get('title')
    description = data.get('description')
    
    try:
        task = Task.objects.get(id=task_id)
        if not task.project.can_user_edit(request.user):
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        task.title = title
        task.description = description
        task.save()
        return JsonResponse({'success': True})
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)

@login_required
@require_http_methods(['POST'])
def delete_project(request):
    data = json.loads(request.body)
    project_id = data.get('project_id')
    
    try:
        project = Project.objects.get(id=project_id)
        if request.user != project.owner:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        project.delete()
        return JsonResponse({'success': True})
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)

@login_required
@require_http_methods(['POST'])
def delete_task(request):
    data = json.loads(request.body)
    task_id = data.get('task_id')
    
    try:
        task = Task.objects.get(id=task_id)
        if not task.project.can_user_edit(request.user):
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        task.delete()
        return JsonResponse({'success': True})
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)

@login_required
@require_http_methods(['POST'])
def add_participant(request):
    data = json.loads(request.body)
    project_id = data.get('project_id')
    username = data.get('username')
    
    try:
        project = Project.objects.get(id=project_id)
        if request.user != project.owner:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        user = User.objects.get(username=username)
        project.participants.add(user)
        return JsonResponse({'success': True})
    except (Project.DoesNotExist, User.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Project or user not found'}, status=404)

@login_required
@require_http_methods(['POST'])
def remove_participant(request):
    data = json.loads(request.body)
    project_id = data.get('project_id')
    username = data.get('username')
    
    try:
        project = Project.objects.get(id=project_id)
        if request.user != project.owner:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        user = User.objects.get(username=username)
        project.participants.remove(user)
        return JsonResponse({'success': True})
    except (Project.DoesNotExist, User.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Project or user not found'}, status=404)

@login_required
def get_participants(request):
    project_id = request.GET.get('project_id')
    
    try:
        project = Project.objects.get(id=project_id)
        if not project.can_user_edit(request.user):
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        participants = [{'username': user.username} for user in project.participants.all()]
        return JsonResponse({'success': True, 'participants': participants})
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
