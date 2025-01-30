from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json
from .models import Project, Task, Diary
from datetime import datetime

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
            Task.objects.create(
                project=project,
                title=request.POST['title'],
                description=request.POST.get('description', '')
            )
            return redirect('projects')
        else:  # Adding new project
            project = Project.objects.create(
                created_by=request.user,
                title=request.POST['title'],
                description=request.POST.get('description', ''),
                is_public=True
            )
            return redirect('projects')
    
    all_projects = Project.objects.all().order_by('-created_at')
    return render(request, 'main/projects.html', {'projects': all_projects})

@login_required
@require_http_methods(['POST'])
def update_task_status(request):
    data = json.loads(request.body)
    task_id = data.get('task_id')
    new_status = data.get('new_status')
    
    try:
        task = Task.objects.get(id=task_id)
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
        participants = [{'username': user.username} for user in project.participants.all()]
        return JsonResponse({'success': True, 'participants': participants})
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)

@login_required
def calendar(request):
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Tüm günlük girişlerinin tarihlerini al
    diary_dates = list(Diary.objects.all().values_list('date', flat=True))
    diary_dates = [date.strftime('%Y-%m-%d') for date in diary_dates]
    
    return render(request, 'main/calendar.html', {
        'current_month': current_month,
        'current_year': current_year,
        'diary_dates': diary_dates
    })

@login_required
def get_diary_entries(request, date):
    try:
        entries = Diary.objects.filter(date=date)
        entries_data = [{
            'id': entry.id,
            'title': entry.title,
            'content': entry.content,
            'created_by': entry.created_by.username
        } for entry in entries]
        return JsonResponse({'success': True, 'entries': entries_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def save_diary(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            date_str = data.get('date')
            title = data.get('title')
            content = data.get('content')
            
            if not all([date_str, title, content]):
                return JsonResponse({'success': False, 'error': 'Eksik bilgi'})
            
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Geçersiz tarih formatı'})
            
            diary = Diary.objects.create(
                date=date,
                title=title,
                content=content,
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'diary': {
                    'title': diary.title,
                    'content': diary.content,
                    'created_by': diary.created_by.username,
                    'date': diary.date.strftime('%Y-%m-%d')
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Geçersiz JSON verisi'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Geçersiz istek metodu'})
