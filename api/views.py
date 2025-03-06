from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from FileNest import settings
from helpers.minio.storage import minio_remove, minio_upload
from .serializers import UserSerializer
from .serializers import FileMetadataSerializer  # You need to create this serializer
from upload.models import FileMetadata

@api_view(['GET'])
def hello(request):
    name = request.GET.get('name', 'guest')
    data = {
        'name': name,
        'message': f"Hello {name}, your first API endpoint has been created successfully!"
    }
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([BasicAuthentication, SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        user = User.objects.get(username=request.data['username'])
        user.set_password(request.data['password'])
        user.save()
        token = Token.objects.create(user=user)
        return Response({'token': token.key, 'user': serializer.data})
    return Response(serializer.errors, status=status.HTTP_200_OK)

@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, username=request.data['username'])
    if not user.check_password(request.data['password']):
        return Response("missing user", status=status.HTTP_404_NOT_FOUND)
    token, created = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(user)
    return Response({'token': token.key, 'user': serializer.data})

@api_view(['GET'])
@authentication_classes([BasicAuthentication, SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def test_token(request):
    user = request.user  # Authenticated user from token
    serializer = UserSerializer(user)
    return Response({
        "message": "Token is valid",
        "user": serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([BasicAuthentication, SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_upload_file(request):
    """API to upload a file for authenticated users."""
    if 'image_file' not in request.FILES:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    image_file = request.FILES['image_file']
    if image_file:
        file_name, file_url, etag, chunk_count = minio_upload(image_file)

        # Store metadata (e.g., number of chunks) in your Django model
        upload = FileMetadata.objects.create(
            file_name=file_name,
            file_url=file_url,
            file_size=image_file.size,
            etag=etag,
            location=settings.MINIO_BUCKET_NAME,
            uploaded_by=request.user,
            total_chunks=chunk_count
        )

        return Response({
            "message": "File uploaded successfully",
            "file_url": file_url,
            "uploaded_by": upload.uploaded_by.username,
            "uploaded_at": upload.uploaded_at
        }, status=status.HTTP_201_CREATED)

    return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@authentication_classes([BasicAuthentication, SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_delete_file(request, file_id):
    try:
        """API to delete a file for authorized users only."""
        file_obj = get_object_or_404(FileMetadata, id=file_id)

        if file_obj.uploaded_by != request.user and not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        # Confirm file is removed before deleting from DB
        if file_obj.file_name:
            minio_remove(file_obj.file_name)
            file_obj.delete()
        return Response({"message": "File deleted successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": "File could not be deleted from storage"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([BasicAuthentication, SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_list_files(request):
    """API to list all uploaded files for the authenticated user."""
    uploads = FileMetadata.objects.filter(uploaded_by=request.user) if not request.user.is_staff else FileMetadata.objects.all()
    serializer = FileMetadataSerializer(uploads, many=True)
    return Response({ "message": "List of uploaded files", "files_count": len(serializer.data), "files": serializer.data}, status=status.HTTP_200_OK)
