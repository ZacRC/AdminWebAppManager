from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Project
from django.conf import settings
import os
import shutil
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import os
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import FileOperation

# Create your views here.

@login_required
def dashboard(request):
    projects = Project.objects.filter(user=request.user)
    return render(request, 'mainapp/dashboard.html', {'projects': projects})

@login_required
def upload_project(request):
    if request.method == 'POST' and request.FILES['project_folder']:
        project_folder = request.FILES['project_folder']
        project_name = project_folder.name
        user_projects_path = os.path.join(settings.MEDIA_ROOT, f'user_projects/{request.user.id}')
        os.makedirs(user_projects_path, exist_ok=True)
        project_path = os.path.join(user_projects_path, project_name)
        
        print(f"Uploading project: {project_name}")  # Debug print
        print(f"User projects path: {user_projects_path}")  # Debug print
        print(f"Project path: {project_path}")  # Debug print
        
        with open(project_path, 'wb+') as destination:
            for chunk in project_folder.chunks():
                destination.write(chunk)
        
        # Extract the uploaded zip file
        extract_path = os.path.join(user_projects_path, os.path.splitext(project_name)[0])
        print(f"Extracting to: {extract_path}")  # Debug print
        shutil.unpack_archive(project_path, extract_path)
        os.remove(project_path)  # Remove the zip file after extraction
        
        # Clean up unwanted files and directories
        for root, dirs, files in os.walk(extract_path, topdown=True):
            dirs[:] = [d for d in dirs if not should_ignore(d)]
            for file in files:
                if should_ignore(file):
                    os.remove(os.path.join(root, file))
        
        print(f"Cleaned extracted files: {os.listdir(extract_path)}")  # Debug print
        
        project = Project.objects.create(user=request.user, name=os.path.splitext(project_name)[0], root_path=extract_path)
        print(f"Created project: {project.name} with root path: {project.root_path}")  # Debug print
        return redirect('dashboard')
    return render(request, 'mainapp/upload_project.html')

@login_required
def editor(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    print(f"Project root path: {project.root_path}")  # Debug print
    file_tree = generate_file_tree(project.root_path)
    print(f"Generated file tree: {file_tree}")  # Debug print
    return render(request, 'mainapp/editor.html', {
        'project': project,
        'file_tree_json': json.dumps(file_tree)
    })

def should_ignore(name):
    ignore_list = ['.DS_Store', '__MACOSX']
    return name in ignore_list or name.startswith('.')

def generate_file_tree(root_path):
    print(f"Generating file tree for: {root_path}")  # Debug print
    file_tree = []
    for root, dirs, files in os.walk(root_path):
        # Remove ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(d)]
        
        print(f"Current directory: {root}")  # Debug print
        print(f"Subdirectories: {dirs}")  # Debug print
        print(f"Files: {files}")  # Debug print
        relative_path = os.path.relpath(root, root_path)
        current_level = file_tree
        if relative_path != '.':
            path_parts = relative_path.split(os.sep)
            for part in path_parts:
                existing_dir = next((item for item in current_level if item['name'] == part and item['type'] == 'directory'), None)
                if existing_dir is None:
                    new_dir = {'name': part, 'type': 'directory', 'children': []}
                    current_level.append(new_dir)
                    current_level = new_dir['children']
                else:
                    current_level = existing_dir['children']
        for file in files:
            if not should_ignore(file):
                current_level.append({'name': file, 'type': 'file', 'path': os.path.join(relative_path, file)})
    print(f"Final file tree: {file_tree}")  # Debug print
    return file_tree

@login_required
def load_file(request, project_id):
    project = Project.objects.get(id=project_id, user=request.user)
    file_path = request.GET.get('path')
    full_path = os.path.join(project.root_path, file_path)
    
    if os.path.exists(full_path) and os.path.isfile(full_path):
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return JsonResponse({'content': content})
        except UnicodeDecodeError:
            # If UTF-8 fails, try with ISO-8859-1
            with open(full_path, 'r', encoding='iso-8859-1') as file:
                content = file.read()
            return JsonResponse({'content': content})
    else:
        return JsonResponse({'error': 'File not found'}, status=404)

@login_required
@require_POST
def save_file(request, project_id):
    project = Project.objects.get(id=project_id, user=request.user)
    data = json.loads(request.body)
    file_path = data.get('path')
    content = data.get('content')
    full_path = os.path.join(project.root_path, file_path)
    
    if os.path.exists(os.path.dirname(full_path)):
        with open(full_path, 'w') as file:
            file.write(content)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error': 'Invalid file path'}, status=400)

@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    project_path = project.root_path
    
    # Delete the project files
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
    
    # Delete the project from the database
    project.delete()
    
    messages.success(request, f'Project "{project.name}" has been deleted.')
    return redirect('dashboard')

@login_required
@require_POST
def create_file_or_folder(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    data = json.loads(request.body)
    path = data.get('path')
    name = data.get('name')
    is_folder = data.get('is_folder', False)
    
    full_path = os.path.join(project.root_path, path, name)
    
    if is_folder:
        os.makedirs(full_path, exist_ok=True)
    else:
        open(full_path, 'a').close()
    
    FileOperation.objects.create(project=project, operation_type='create', source_path=os.path.join(path, name))
    return JsonResponse({'success': True})

@login_required
@require_POST
def move_file_or_folder(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    data = json.loads(request.body)
    source = data.get('source')
    destination = data.get('destination')
    
    source_path = os.path.join(project.root_path, source)
    destination_path = os.path.join(project.root_path, destination)
    
    shutil.move(source_path, destination_path)
    
    FileOperation.objects.create(project=project, operation_type='move', source_path=source, destination_path=destination)
    return JsonResponse({'success': True})

@login_required
@require_POST
def copy_file_or_folder(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    data = json.loads(request.body)
    source = data.get('source')
    destination = data.get('destination')
    
    source_path = os.path.join(project.root_path, source)
    destination_path = os.path.join(project.root_path, destination)
    
    if os.path.isdir(source_path):
        shutil.copytree(source_path, destination_path)
    else:
        shutil.copy2(source_path, destination_path)
    
    FileOperation.objects.create(project=project, operation_type='copy', source_path=source, destination_path=destination)
    return JsonResponse({'success': True})

@login_required
@require_POST
def delete_file_or_folder(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    data = json.loads(request.body)
    path = data.get('path')
    
    full_path = os.path.join(project.root_path, path)
    
    if os.path.isdir(full_path):
        shutil.rmtree(full_path)
    else:
        os.remove(full_path)
    
    FileOperation.objects.create(project=project, operation_type='delete', source_path=path)
    return JsonResponse({'success': True})
