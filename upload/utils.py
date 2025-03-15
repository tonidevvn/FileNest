"""Utility functions for file upload and management."""
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied

from monitoring.views import log_file_action
from helpers.minio.storage import minio_upload, minio_remove
from .models import FileMetadata, FileChunk

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
MAX_FILENAME_LENGTH = 128

def validate_file(file_obj):
    """Validate file size and name length."""
    errors = []
    
    if len(file_obj.name) > MAX_FILENAME_LENGTH:
        errors.append(f"File name '{file_obj.name}' exceeds {MAX_FILENAME_LENGTH} characters.")

    if file_obj.size > MAX_FILE_SIZE:
        errors.append(f"File '{file_obj.name}' exceeds {MAX_FILE_SIZE/(1024*1024)}MB limit.")

    return errors

def handle_file_upload(request, file_obj):
    """Process file upload and create metadata records."""
    file_name, file_url, etag, chunk_count, chunk_parts, checksum = minio_upload(file_obj)

    file_metadata = FileMetadata.objects.create(
        file_name=file_name,
        file_url=file_url,
        file_size=file_obj.size,
        etag=etag,
        location=settings.MINIO_BUCKET_NAME,
        uploaded_by=request.user,
        total_chunks=chunk_count,
        content_type=file_obj.content_type,
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
    return {"file_url": f'/detail/{file_metadata.id}', "file_name": file_name}

def delete_file(request, file_id):
    """Delete file and related chunks."""
    file_obj = get_object_or_404(FileMetadata, id=file_id)

    if file_obj.uploaded_by != request.user and not request.user.is_staff:
        raise PermissionDenied("Unauthorized access")

    chunks = FileChunk.objects.filter(file_metadata=file_obj)
    for chunk in chunks:
        minio_remove(chunk.chunk_file)
        chunk.delete()

    if file_obj.file_name:
        minio_remove(file_obj.file_name)
        log_file_action(request.user, file_obj.file_name, "DELETE", request)
        file_obj.delete()
        return JsonResponse({"message": "File deleted successfully"})

    return JsonResponse({"error": "File could not be deleted"}, status=500)
