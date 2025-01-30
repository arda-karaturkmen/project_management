from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('projects/', views.projects, name='projects'),
    path('project/task/status/', views.update_task_status, name='update_task_status'),
    path('project/task/update/', views.update_task, name='update_task'),
    path('project/delete/', views.delete_project, name='delete_project'),
    path('project/task/delete/', views.delete_task, name='delete_task'),
    path('project/participant/add/', views.add_participant, name='add_participant'),
    path('project/participant/remove/', views.remove_participant, name='remove_participant'),
    path('project/participants/', views.get_participants, name='get_participants'),
    path('calendar/', views.calendar, name='calendar'),
    path('diary/entries/<str:date>/', views.get_diary_entries, name='get_diary_entries'),
    path('diary/save/', views.save_diary, name='save_diary'),
]
