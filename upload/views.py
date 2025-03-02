from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import FileMetadata, FileChunk

@login_required(login_url='/login/')
def image_upload(request):
    """Handles file upload and ensures the file list updates correctly."""
    image_url = ""
    if request.method == 'POST':
        image_file = request.FILES.get('image_file')
        storage_type = request.POST.get('storage_type', 'cloud')  # Default to cloud storage

        if image_file:
            upload = FileMetadata(uploaded_by=request.user,
                                  storage_type=storage_type)

            # Upload file to the correct storage field
            if storage_type == 'cloud':
                upload.file_cloud = image_file  # Store file in Cloud Storage
                upload.file_localhost = None  # Ensure the local field is empty
            else:
                upload.file_localhost = image_file  # Store file in Local Storage
                upload.file_cloud = None  # Ensure the cloud field is empty

            upload.save()
            image_url = upload.file_url

    # Refresh the file list after any operation
    uploads = FileMetadata.objects.all() if request.user.is_staff else FileMetadata.objects.filter(
        uploaded_by=request.user)
    return render(request, 'upload.html', {'image_url': image_url, 'uploads': uploads})

@login_required(login_url='/login/')
def load_storage(request):
    # Refresh the file list after any operation
    uploads = FileMetadata.objects.all() if request.user.is_staff else FileMetadata.objects.filter(
        uploaded_by=request.user)
    return render(request, 'storage.html', {'uploads': uploads})

@login_required(login_url='/login/')
def view_chunks(request, file_key):
    """Displays chunk details for a specific file."""
    file_metadata = get_object_or_404(FileMetadata, file_key=file_key)

    # Fetch chunks related to this file
    chunks = FileChunk.objects.filter(file_metadata=file_metadata).order_by('chunk_index')

    return render(request, 'chunks.html', {'file_metadata': file_metadata, 'chunks': chunks})

@login_required(login_url='/login/')
def delete_file(request, file_key):
    """Deletes a file from the database and cloud storage."""
    file_obj = get_object_or_404(FileMetadata, file_key=file_key)

    if file_obj.uploaded_by != request.user and not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # Confirm file is removed before deleting from DB
    if file_obj.file_cloud or file_obj.file_localhost:
        file_obj.delete()
        return JsonResponse({"message": "File deleted successfully"}, status=200)
    else:
        return JsonResponse({"error": "File could not be deleted from storage"}, status=500)

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