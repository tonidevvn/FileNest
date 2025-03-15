"""API Views for FileNest."""
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from FileNest import settings
from helpers.minio.storage import minio_download, minio_remove, minio_upload
from upload.models import FileChunk, FileMetadata
from .serializers import FileMetadataSerializer, UserSerializer

# Common authentication and permission classes
AUTH_CLASSES = [BasicAuthentication, SessionAuthentication, TokenAuthentication]
PERM_CLASSES = [IsAuthenticated]

def create_response(success=True, message="", data=None, status_code=status.HTTP_200_OK):
    """Create a standardized response format."""
    return Response(
        {
            "success": success,
            "message": message,
            "data": data or {},
        },
        status=status_code,
    )

@api_view(["POST"])
def signup(request):
    """Register a new user and return their token."""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        user = User.objects.get(username=request.data["username"])
        user.set_password(request.data["password"])
        user.save()
        token = Token.objects.create(user=user)
        return create_response(
            message="User registered successfully",
            data={"token": token.key, "user": serializer.data},
            status_code=status.HTTP_201_CREATED,
        )
    return create_response(
        success=False,
        message="Invalid registration data",
        data=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST,
    )

@api_view(["POST"])
def login(request):
    """Log in a user and return their token."""
    user = get_object_or_404(User, username=request.data["username"])
    if not user.check_password(request.data["password"]):
        return create_response(
            success=False,
            message="Invalid credentials",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    token, _ = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(user)
    return create_response(
        message="Login successful",
        data={"token": token.key, "user": serializer.data},
    )

@api_view(["POST"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def upload_file(request):
    """Upload a file for authenticated users."""
    if "file-upload" not in request.FILES:
        return create_response(
            success=False,
            message="No file provided",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    file_upload = request.FILES["file-upload"]
    file_name, file_url, etag, chunk_count, chunk_parts, checksum = minio_upload(file_upload)

    # Store metadata in Django model
    file_obj = FileMetadata.objects.create(
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

    chunks_list = []
    if chunk_count > 1:
        for i, part in enumerate(chunk_parts):
            chunk = FileChunk.objects.create(
                file_metadata=file_obj,
                chunk_index=i,
                chunk_file=part.get("name"),
                chunk_size=part.get("size"),
                etag=part.get("etag"),
            )
            chunks_list.append({
                "chunk_index": chunk.chunk_index,
                "chunk_size": chunk.chunk_size,
                "etag": chunk.etag,
            })

    return create_response(
        message="File uploaded successfully",
        data=FileMetadataSerializer(file_obj).data,
        status_code=status.HTTP_201_CREATED,
    )

@api_view(["GET"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def detail_file(request, file_id):
    """Get file details for authorized users."""
    try:
        file_obj = get_object_or_404(FileMetadata, id=file_id)
        if file_obj.uploaded_by != request.user and not request.user.is_staff:
            return create_response(
                success=False,
                message="Unauthorized access",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = FileMetadataSerializer(file_obj)
        return create_response(
            message="File details retrieved",
            data=serializer.data,
        )
    except Exception as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["DELETE"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def delete_file(request, file_id):
    """Delete a file for authorized users."""
    try:
        file_obj = get_object_or_404(FileMetadata, id=file_id)
        if file_obj.uploaded_by != request.user and not request.user.is_staff:
            return create_response(
                success=False,
                message="Unauthorized access",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        minio_remove(file_obj)
        file_obj.delete()
        return create_response(message="File deleted successfully")
    except Exception as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["GET"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def list_files(request):
    """List all uploaded files for the authenticated user."""
    uploads = (
        FileMetadata.objects.filter(uploaded_by=request.user)
        if not request.user.is_staff
        else FileMetadata.objects.all()
    )
    serializer = FileMetadataSerializer(uploads, many=True)
    return create_response(
        message="Files retrieved successfully",
        data={"files": serializer.data, "count": len(serializer.data)},
    )

@api_view(["GET"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def download_file(request, file_id):
    """Download a file for authenticated users."""
    try:
        file_obj = get_object_or_404(FileMetadata, id=file_id)
        if file_obj.uploaded_by != request.user and not request.user.is_staff:
            return create_response(
                success=False,
                message="Unauthorized access",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        use_cache = request.GET.get("no_cache", "0") != "1"
        file_data, file_size, content_type = minio_download(file_obj, use_cache=use_cache)

        response = HttpResponse(file_data, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{file_obj.file_name.split("-", 1)[1]}"'
        response["Content-Length"] = file_size
        return response

    except Exception as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
