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
from .models import FileMetadata, FileChunk, FileAccessLog


MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB in bytes
MAX_FILENAME_LENGTH = 128  # Maximum file name length

@login_required(login_url='/login/')
def file_upload(request):
    """Handles multiple file uploads and ensures file list updates correctly."""
    uploaded_files = []
    if request.method == 'POST':
        files = request.FILES.getlist('file-upload')
        errors = []

        if not files:
            errors.append("Please select at least one file before uploading.")

        for upload_file in files:
            if len(upload_file.name) > MAX_FILENAME_LENGTH:
                errors.append(f"File name '{upload_file.name}' exceeds 128 characters.")

            if upload_file.size > MAX_FILE_SIZE:
                errors.append(f"File '{upload_file.name}' exceeds the 500MB limit.")

        if errors:
            return render(request, 'upload_resp.html', {"errors": errors})  # Return errors if any

        for file_upload in files:
            file_name, file_url, etag, chunk_count, chunk_parts, checksum = minio_upload(file_upload)

            # Store metadata
            file_metadata = FileMetadata.objects.create(
                file_name=file_name,
                file_url=file_url,
                file_size=file_upload.size,
                etag=etag,
                location=settings.MINIO_BUCKET_NAME,
                uploaded_by=request.user,
                total_chunks=chunk_count,
                content_type=file_upload.content_type,
                checksum=checksum,
            )

            if chunk_count > 1:
                for i, chunk_part in enumerate(chunk_parts):
                    FileChunk.objects.create(
                        file_metadata=file_metadata,
                        chunk_index=i,
                        chunk_file=chunk_part.get("name"),
                        chunk_size=chunk_part.get("size"),
                        etag=chunk_part.get("etag"),
                    )
            log_file_action(request.user, file_name, 'UPLOAD', request)
            uploaded_files.append({"file_url": f'/detail/{file_metadata.id}', "file_name": file_name})
            time.sleep(0.5)

        return render(request, 'upload_resp.html', {'uploaded_files': uploaded_files})

    return render(request, 'upload.html')


@login_required(login_url='/login/')
def file_detail(request, file_id):
    """Displays chunk details for a specific file."""
    file_metadata = get_object_or_404(FileMetadata, id=file_id)
    chunks = FileChunk.objects.filter(file_metadata=file_metadata).order_by('chunk_index')
    log_file_action(request.user, file_metadata.file_name, 'VIEW', request)

    nodes = node_manager.get_all_nodes()
    distributed_files = [
        {
            "status": node.check_file_status(file_metadata.file_name),
            "file_url": f"http://{node.access_url}/{file_metadata.file_name}",
            "region": node.region,
        }
        for node in nodes
    ]

    return render(request, 'detail.html', {'file_metadata': file_metadata, 'chunks': chunks, "distributed_files": distributed_files})


@login_required(login_url='/login/')
def file_delete(request, file_id):
    """Deletes a file from the database and cloud storage."""
    file_obj = get_object_or_404(FileMetadata, id=file_id)

    if file_obj.uploaded_by != request.user and not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        # Get all related chunks (if any)
        file_chunks = FileChunk.objects.filter(file_metadata=file_obj)

        # 🔹 Ensure there are chunks before deleting them
        if file_chunks.exists():
            for chunk in file_chunks:
                print(f"🗑️ Deleting chunk: {chunk.chunk_file}")  # Debugging
                minio_remove(chunk.chunk_file)
                chunk.delete()

        # 🔹 Delete the main file
        if file_obj.file_name:
            print(f"🗑️ Deleting file: {file_obj.file_name}")  # Debugging
            minio_remove(file_obj.file_name)

            # 🔹 Log file deletion before deleting record
            log_file_action(request.user, file_obj.file_name, "DELETE", request)
            file_obj.delete()
            print(f"✅ Log created for DELETE: {file_obj.file_name}")  # Debugging
            return JsonResponse({"message": "File deleted successfully"}, status=200)

    except Exception as e:
        print(f"❌ Error removing file: {e}")  # Debugging
        return JsonResponse({"error": "Error deleting file"}, status=500)
    return JsonResponse({"error": "File could not be deleted from storage"}, status=500)

@login_required(login_url='/login/')
def load_storage(request):
    """Loads the storage page with a paginated list of files."""
    uploads_list = FileMetadata.objects.all() if request.user.is_staff else FileMetadata.objects.filter(uploaded_by=request.user)

    paginator = Paginator(uploads_list, 20)  # Show 20 files per page
    page_number = request.GET.get('page', 1)
    uploads = paginator.get_page(page_number)
    total = uploads_list.count()

    return render(request, 'storage.html', {'uploads': uploads, "total": total})


@login_required(login_url='/login/')
def admin_dashboard(request):
    """Displays the admin dashboard with file and node status."""
    #uploads_list = FileMetadata.objects.all() if request.user.is_staff else FileMetadata.objects.filter(uploaded_by=request.user)
    uploads_list = FileMetadata.objects.select_related(
        'uploaded_by').all() if request.user.is_staff else FileMetadata.objects.filter(uploaded_by=request.user)
    paginator = Paginator(uploads_list, 20)  # Show 20 files per page
    page_number = request.GET.get('page', 1)
    uploads = paginator.get_page(page_number)
    total = uploads_list.count()

    nodes = node_manager.get_all_nodes()
    return render(request, 'dashboard.html', {'uploads': uploads, "total": total, "nodes": nodes})


def user_login(request):
    """Handles user login."""
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')  # Redirect to home page after login
        return render(request, 'login.html', {'error': 'Invalid username or password'})

    return render(request, 'login.html')


def user_logout(request):
    """Logs out the user and redirects to login page."""
    logout(request)
    return redirect('/login/')


def user_signup(request):
    """Handles user registration."""
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            return render(request, 'signup.html', {'error': 'Passwords do not match'})

        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already taken'})

        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error': 'Email is already registered'})

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)  # Automatically log in after sign-up
        return redirect('/')  # Redirect to homepage after signup

    return render(request, 'signup.html')

from django.contrib.admin.views.decorators import staff_member_required


def log_file_action(user, file_name, action, request):
    print(f"📌 Logging action: {action} on {file_name} by {user}")  # Debug Print

    log_entry = FileAccessLog.objects.create(
        user=user,
        file_name=file_name,
        action=action,
        ip_address=request.META.get('REMOTE_ADDR', 'Unknown')
    )

    print(f"✅ Log saved: {log_entry}")  # Debug confirmation

@staff_member_required
def admin_log_monitoring(request):
    logs = FileAccessLog.objects.all().order_by('-timestamp')

    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page', 1)
    logs_page = paginator.get_page(page_number)

    return render(request, 'admin_log.html', {'logs': logs_page})