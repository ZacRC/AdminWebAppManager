from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload_project/', views.upload_project, name='upload_project'),
    path('editor/<int:project_id>/', views.editor, name='editor'),
    path('load_file/<int:project_id>/', views.load_file, name='load_file'),
    path('save_file/<int:project_id>/', views.save_file, name='save_file'),
    path('delete_project/<int:project_id>/', views.delete_project, name='delete_project'),
    path('create_file_or_folder/<int:project_id>/', views.create_file_or_folder, name='create_file_or_folder'),
    path('move_file_or_folder/<int:project_id>/', views.move_file_or_folder, name='move_file_or_folder'),
    path('copy_file_or_folder/<int:project_id>/', views.copy_file_or_folder, name='copy_file_or_folder'),
    path('delete_file_or_folder/<int:project_id>/', views.delete_file_or_folder, name='delete_file_or_folder'),
]
