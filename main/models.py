from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class DiaryEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']  # Bir kullanıcı bir güne sadece bir günlük yazabilir

    def __str__(self):
        return f"{self.user.username}'s diary on {self.date}"

class Project(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    participants = models.ManyToManyField(User, related_name='participating_projects', blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)  # True: herkes görebilir, False: sadece katılımcılar

    def __str__(self):
        return self.title

    def can_user_access(self, user):
        return (self.is_public or 
                user == self.owner or 
                self.participants.filter(id=user.id).exists())

    def can_user_edit(self, user):
        return (user == self.owner or 
                self.participants.filter(id=user.id).exists())

class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.IntegerField(default=0)  # Sürükle-bırak sıralaması için

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
