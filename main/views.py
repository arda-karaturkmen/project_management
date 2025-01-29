from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.utils import timezone
from .models import DiaryEntry, Project, Task
from datetime import datetime, date
import calendar
import json
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.views.decorators.cache import cache_page
from django.core.cache import cache

# Create your views here.

@login_required
def home(request):
    return render(request, 'main/home.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Hesap oluşturuldu! Şimdi giriş yapabilirsiniz.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})

@login_required
@cache_page(60 * 15)  # Cache for 15 minutes
def calendar(request):
    # URL'den ay ve yıl parametrelerini al
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    if month and year:
        current_month = int(month)
        current_year = int(year)
    else:
        today = datetime.now()
        current_month = today.month
        current_year = today.year
    
    # Cache key oluştur
    cache_key = f'diary_entries_{current_year}_{current_month}'
    entries = cache.get(cache_key)
    
    if entries is None:
        # Bu aydaki tüm günlükleri al
        entries = DiaryEntry.objects.filter(
            date__year=current_year,
            date__month=current_month
        ).select_related('user')  # Kullanıcı bilgilerini de getir
        
        # Cache'e kaydet
        cache.set(cache_key, entries, 60 * 15)  # 15 dakika cache'te tut
    
    # Günlük olan günleri işaretle
    diary_dates = {}
    for entry in entries:
        day = entry.date.day
        if day not in diary_dates:
            diary_dates[day] = []
        diary_dates[day].append({
            'username': entry.user.username,
            'title': entry.title
        })
    
    return render(request, 'main/calendar.html', {
        'diary_dates': json.dumps(diary_dates),
        'current_month': current_month,
        'current_year': current_year
    })

@login_required
def get_diary(request, year, month, day):
    target_date = date(year, month, day)
    entries = DiaryEntry.objects.filter(date=target_date)
    
    entries_data = []
    for entry in entries:
        entries_data.append({
            'username': entry.user.username,
            'title': entry.title,
            'content': entry.content,
            'created_at': entry.created_at.strftime('%H:%M')
        })
    
    return JsonResponse({
        'status': 'success' if entries_data else 'empty',
        'entries': entries_data
    })

@login_required
def save_diary(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        entry = DiaryEntry.objects.filter(user=request.user, date=date).first()
        if entry:
            entry.title = data['title']
            entry.content = data['content']
            entry.save()
        else:
            DiaryEntry.objects.create(
                user=request.user,
                date=date,
                title=data['title'],
                content=data['content']
            )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'})

@login_required
def projects(request):
    if request.method == 'POST':
        if 'project_id' in request.POST:  # Yeni görev ekleme
            project = get_object_or_404(Project, id=request.POST['project_id'])
            if not project.can_user_edit(request.user):
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            task = Task.objects.create(
                project=project,
                title=request.POST['title'],
                description=request.POST['description']
            )
            return redirect('projects')
        else:  # Yeni proje ekleme
            project = Project.objects.create(
                owner=request.user,
                title=request.POST['title'],
                description=request.POST['description'],
                is_public=True  # Varsayılan olarak herkese açık
            )
            return redirect('projects')
    
    # Kullanıcının erişebileceği tüm projeleri getir
    accessible_projects = Project.objects.filter(
        Q(is_public=True) |  # Herkese açık projeler
        Q(owner=request.user) |  # Kullanıcının kendi projeleri
        Q(participants=request.user)  # Katılımcı olduğu projeler
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
        if request.user != project.owner:  # Sadece proje sahibi silebilir
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
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)

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
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)

@login_required
def get_participants(request):
    project_id = request.GET.get('project_id')
    
    try:
        project = Project.objects.get(id=project_id)
        if request.user != project.owner:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        participants = [{'username': user.username} for user in project.participants.all()]
        return JsonResponse({'success': True, 'participants': participants})
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
