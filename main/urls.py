from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('calendar/', views.calendar, name='calendar'),
    path('projects/', views.projects, name='projects'),
    path('update_task_status/', views.update_task_status, name='update_task_status'),
    path('update_task/', views.update_task, name='update_task'),
    path('delete_project/', views.delete_project, name='delete_project'),
    path('delete_task/', views.delete_task, name='delete_task'),
    path('diary/<int:year>/<int:month>/<int:day>/', views.get_diary, name='get_diary'),
    path('diary/save/', views.save_diary, name='save_diary'),
    path('add_participant/', views.add_participant, name='add_participant'),
    path('remove_participant/', views.remove_participant, name='remove_participant'),
    path('get_participants/', views.get_participants, name='get_participants'),
]
