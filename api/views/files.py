"""File operation related views."""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from FileNest import settings
from helpers.minio.storage import minio_download, minio_remove, minio_upload
from upload.models import FileChunk, FileMetadata
from api.serializers import FileMetadataSerializer
from .base import DEFAULT_AUTHENTICATION_CLASSES, DEFAULT_PERMISSION_CLASSES

@api_view(["POST"])
@authentication_classes(DEFAULT_AUTHENTICATION_CLASSES)
@permission_classes(DEFAULT_PERMISSION_CLASSES)
def upload_file(request):
    """Upload a file for authenticated users."""
    if "upload_file" not in request.FILES:
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    file_upload = request.FILES["file-upload"]
    if file_upload:
        file_name, file_url, etag, chunk_count, chunk_parts, checksum = minio_upload(
            file_upload
        )

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
            for i in range(chunk_count):
                chunk = FileChunk.objects.create(
                    file_metadata=file_obj,
                    chunk_index=i,
                    chunk_file=chunk_parts[i].get("name"),
                    chunk_size=chunk_parts[i].get("size"),
                    etag=chunk_parts[i].get("etag"),
                )
                chunks_list.append({
                    "chunk_index": chunk.chunk_index,
                    "chunk_file": chunk.chunk_file,
                    "chunk_size": chunk.chunk_size,
                    "etag": chunk.etag,
                    "uploaded_at": chunk.uploaded_at,
                })

        return Response({
            "message": "File uploaded successfully",
            "id": file_obj.id,
            "file_name": file_name,
            "file_url": file_url,
            "file_size": file_obj.file_size,
            "content-type": file_upload.content_type,
            "etag": etag,
            "bucket": settings.MINIO_BUCKET_NAME,
            "checksum": checksum,
            "total_chunks": file_obj.total_chunks,
            "chunks": chunks_list,
            "uploaded_by": file_obj.uploaded_by.username,
            "uploaded_at": file_obj.uploaded_at,
        }, status=status.HTTP_201_CREATED)

    return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@authentication_classes(DEFAULT_AUTHENTICATION_CLASSES)
@permission_classes(DEFAULT_PERMISSION_CLASSES)
def detail_file(request, file_id):
    """Get file details for authorized users."""
    try:
        file_obj = get_object_or_404(FileMetadata, id=file_id)

        if file_obj.uploaded_by != request.user and not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        chunks_list = []
        chunks = (
            FileChunk.objects.filter(file_metadata=file_obj)
            .order_by("chunk_index")
            .all()
        )
        chunk_count = chunks.count()
        if chunk_count > 1:
            for i in range(chunk_count):
                chunk_i = chunks[i]
                chunks_list.append({
                    "chunk_index": chunk_i.chunk_index,
                    "chunk_file": chunk_i.chunk_file,
                    "chunk_size": chunk_i.chunk_size,
                    "etag": chunk_i.etag,
                    "uploaded_at": chunk_i.uploaded_at,
                })

        return Response({
            "message": "File retrieved successfully.",
            "id": file_obj.id,
            "file_name": file_obj.file_name,
            "file_url": file_obj.file_url,
            "file_size": file_obj.file_size,
            "content-type": file_obj.content_type,
            "etag": file_obj.etag,
            "bucket": settings.MINIO_BUCKET_NAME,
            "checksum": file_obj.checksum,
            "total_chunks": file_obj.total_chunks,
            "chunks": chunks_list,
            "uploaded_by": file_obj.uploaded_by.username,
            "uploaded_at": file_obj.uploaded_at,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": "File could not be found from storage"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["DELETE"])
@authentication_classes(DEFAULT_AUTHENTICATION_CLASSES)
@permission_classes(DEFAULT_PERMISSION_CLASSES)
def delete_file(request, file_id):
    """Delete a file for authorized users."""
    try:
        file_obj = get_object_or_404(FileMetadata, id=file_id)

        if file_obj.uploaded_by != request.user and not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        if file_obj:
            minio_remove(file_obj)
            file_obj.delete()
        return Response(
            {"message": "File deleted successfully"}, status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": "File could not be deleted from storage"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["GET"])
@authentication_classes(DEFAULT_AUTHENTICATION_CLASSES)
@permission_classes(DEFAULT_PERMISSION_CLASSES)
def list_files(request):
    """List all uploaded files for the authenticated user."""
    uploads = (
        FileMetadata.objects.filter(uploaded_by=request.user)
        if not request.user.is_staff
        else FileMetadata.objects.all()
    )
    serializer = FileMetadataSerializer(uploads, many=True)
    return Response({
        "message": "List of uploaded files",
        "files_count": len(serializer.data),
        "files": serializer.data,
    }, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes(DEFAULT_AUTHENTICATION_CLASSES)
@permission_classes(DEFAULT_PERMISSION_CLASSES)
def download_file(request, file_id):
    """Download a file for authenticated users with optimized retrieval."""
    try:
        file_obj = get_object_or_404(FileMetadata, id=file_id)

        if file_obj.uploaded_by != request.user and not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        # Get user's location from request parameters if available
        user_lat = request.GET.get("lat", None)
        user_lon = request.GET.get("lon", None)

        # Convert to float if provided
        if user_lat and user_lon:
            try:
                user_lat = float(user_lat)
                user_lon = float(user_lon)
            except ValueError:
                user_lat = user_lon = None

        # Skip cache for large files if requested
        use_cache = request.GET.get("no_cache", "0") != "1"

        # Download file with optimization
        file_data, file_size, content_type = minio_download(
            file_obj, use_cache=use_cache, user_lat=user_lat, user_lon=user_lon
        )

        # Create response with file data
        response = HttpResponse(file_data, content_type=content_type)
        response["Content-Disposition"] = (
            f'attachment; filename="{file_obj.file_name.split("-", 1)[1]}"'
        )
        response["Content-Length"] = file_size

        return response

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
