from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    root_path = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class FileOperation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    operation_type = models.CharField(max_length=20)  # 'create', 'move', 'copy', 'delete'
    source_path = models.CharField(max_length=1000)
    destination_path = models.CharField(max_length=1000, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.operation_type} - {self.source_path}"
