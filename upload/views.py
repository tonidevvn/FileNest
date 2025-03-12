import time
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator

from helpers.minio.node import node_manager
from helpers.minio.storage import minio_upload, minio_remove
from .models import FileMetadata, FileChunk


MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB in bytes
MAX_FILENAME_LENGTH = 128  # Maximum file name length

@login_required(login_url='/login/')
def file_upload(request):
    """Handles multiple file uploads and ensures file list updates correctly."""
    uploaded_files = []
    if request.method == 'POST':
        files = request.FILES.getlist('file-upload')
        errors = []

        for upload_file in files:

            # Validate filename length
            if len(upload_file.name) > MAX_FILENAME_LENGTH:
                errors.append(f"File name cannot exceed 128 characters.")

            # Validate file size
            if upload_file.size > MAX_FILE_SIZE:
                errors.append(f"File size exceeds 500MB limit.")

        if errors:
            return render(request, 'upload_resp.html', {"errors": errors}) # Return errors if any

        else:
            for fileUpload in files:
                if fileUpload:
                    file_name, file_url, etag, chunk_count, chunk_parts, checksum = minio_upload(fileUpload)

                    # Store metadata (e.g., number of chunks) in your Django model
                    file_metadata = FileMetadata.objects.create(
                        file_name=file_name,
                        file_url=file_url,
                        file_size=fileUpload.size,
                        etag=etag,
                        location=settings.MINIO_BUCKET_NAME,
                        uploaded_by=request.user,
                        total_chunks=chunk_count,
                        content_type=fileUpload.content_type,
                        checksum=checksum,
                    )

                    if chunk_count > 1:
                        for i in range(chunk_count):
                            # Save chunk record
                            chunk_part_i = chunk_parts[i]
                            FileChunk.objects.create(
                                file_metadata=file_metadata,
                                chunk_index=i,
                                chunk_file=chunk_part_i.get("name"),
                                chunk_size=chunk_part_i.get("size"),
                                etag=chunk_part_i.get("etag"),
                            )

                    uploaded_files.append({"file_url": f'/detail/{file_metadata.id}', "file_name": file_name})
                    time.sleep(0.5)

            return render(request, 'upload_resp.html', {'uploaded_files': uploaded_files})
    else:
        return render(request, 'upload.html')

@login_required(login_url='/login/')
def file_detail(request, file_id):
    """Displays chunk details for a specific file."""
    file_metadata = get_object_or_404(FileMetadata, id=file_id)

    # Allowed image extensions
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    file_name = file_metadata.file_name
    is_image = any(file_name.lower().endswith(ext) for ext in image_extensions)

    # Fetch chunks related to this file
    chunks = FileChunk.objects.filter(file_metadata=file_metadata).order_by('chunk_index')

    nodes = node_manager.get_all_nodes()
    distributed_files = []
    for node in nodes:
        status = node.check_file_status(file_name)
        file_url = f"http://{node.access_url}/{file_name}"
        distributed_files.append({"status": status, "file_url": file_url, "region": node.region})

    return render(request, 'detail.html', {'file_metadata': file_metadata, 'chunks': chunks,
        'is_image': is_image, "distributed_files": distributed_files})

@login_required(login_url='/login/')
def file_delete(request, file_id):
    """Deletes a file from the database and cloud storage."""
    file_obj = get_object_or_404(FileMetadata, id=file_id)

    if file_obj.uploaded_by != request.user and not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # Confirm file is removed before deleting from DB
    if file_obj.file_name:
        minio_remove(file_obj.file_name)
        file_obj.delete()
        return JsonResponse({"message": "File deleted successfully"}, status=200)
    else:
        return JsonResponse({"error": "File could not be deleted from storage"}, status=500)

@login_required(login_url='/login/')
def load_storage(request):
    uploads_list = FileMetadata.objects.all() if request.user.is_staff else FileMetadata.objects.filter(uploaded_by=request.user)

    # Pagination setup
    paginator = Paginator(uploads_list, 20)  # Show 10 files per page
    page_number = request.GET.get('page', 1)
    uploads = paginator.get_page(page_number)
    return render(request, 'storage.html', {'uploads': uploads})


def user_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')  # Redirect to home page after login
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('/login/')  # Redirect to login page

def user_signup(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            return render(request, 'signup.html', {'error': 'Passwords do not match'})

        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already taken'})

        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error': 'Email is already registered'})

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        login(request, user)  # Automatically log in after sign-up
        return redirect('/')  # Redirect to homepage after signup

    return render(request, 'signup.html')