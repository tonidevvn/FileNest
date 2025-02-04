from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import FileMetadata

@login_required(login_url='/login/')
def image_upload(request):
    if request.user.is_staff:  # Allow admin members to see all files
        uploads = FileMetadata.objects.all()
    else:  # Regular users see only their own uploads
        uploads = FileMetadata.objects.filter(uploaded_by=request.user)

    if request.method == 'POST':
        image_file = request.FILES['image_file']
        upload = FileMetadata(file=image_file, uploaded_by=request.user)
        upload.save()
        if settings.USE_S3:
            image_url = upload.file.url
        else:
            fs = FileSystemStorage()
            filename = fs.save(image_file.name, image_file)
            image_url = fs.url(filename)
        return render(request, 'upload.html', {
            'image_url': image_url, 'uploads': uploads
        })
    return render(request, 'upload.html', {'uploads': uploads})

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