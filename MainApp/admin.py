from django.contrib import admin
from .models import Project
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'updated_at')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)

admin.site.register(Project, ProjectAdmin)