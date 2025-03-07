from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from helpers.minio.storage import minio_upload, minio_remove
from .models import FileMetadata, FileChunk

@login_required(login_url='/login/')
def file_upload(request):
    """Handles file upload and ensures the file list updates correctly."""
    file_url = ""
    if request.method == 'POST':
        upload_file = request.FILES.get('upload_file')

        if upload_file:
            file_name, file_url, etag, chunk_count, chunk_parts, checksum = minio_upload(upload_file)

            # Store metadata (e.g., number of chunks) in your Django model
            file_metadata = FileMetadata.objects.create(
                file_name=file_name,
                file_url=file_url,
                file_size=upload_file.size,
                etag=etag,
                location=settings.MINIO_BUCKET_NAME,
                uploaded_by=request.user,
                total_chunks=chunk_count,
                content_type=upload_file.content_type,
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

    # Refresh the file list after any operation
    uploads = FileMetadata.objects.all() if request.user.is_staff else FileMetadata.objects.filter(
        uploaded_by=request.user)
    return render(request, 'upload.html', {'file_url': file_url, 'uploads': uploads})

@login_required(login_url='/login/')
def detail(request, file_id):
    """Displays chunk details for a specific file."""
    file_metadata = get_object_or_404(FileMetadata, id=file_id)

    # Allowed image extensions
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    file_name = file_metadata.file_name.lower()
    is_image = any(file_name.endswith(ext) for ext in image_extensions)

    # Fetch chunks related to this file
    chunks = FileChunk.objects.filter(file_metadata=file_metadata).order_by('chunk_index')

    return render(request, 'detail.html', {'file_metadata': file_metadata, 'chunks': chunks,
        'is_image': is_image})

@login_required(login_url='/login/')
def delete_file(request, file_id):
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
    # Refresh the file list after any operation
    uploads = FileMetadata.objects.all() if request.user.is_staff else FileMetadata.objects.filter(
        uploaded_by=request.user)
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