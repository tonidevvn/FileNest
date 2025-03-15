import os
from datetime import timedelta

import minio
from django.conf import settings

# Configure MinIO client
_client = minio.Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)

def minio_storage():
    """Return the MinIO client instance."""
    return _client

def minio_upload(file_obj):
    """Upload a file to MinIO, handling both single and multipart uploads."""
    client = minio_storage()
    file_name = file_obj.name
    file_size = file_obj.size
    content_type = file_obj.content_type

    if not client.bucket_exists(settings.MINIO_BUCKET_NAME):
        client.make_bucket(settings.MINIO_BUCKET_NAME)

    # Handle chunked uploads
    if hasattr(file_obj, 'chunks'):
        parts = []
        for i, chunk in enumerate(file_obj.chunks()):
            part = client.put_object(
                settings.MINIO_BUCKET_NAME,
                f"{file_name}.part{i}",
                chunk,
                length=chunk.size
            )
            parts.append({"part_number": i + 1, "etag": part.etag, "size": chunk.size, "name": f"{file_name}.part{i}"})

        # Complete multipart upload
        file_url = f"{settings.MINIO_ACCESS_URL}/{file_name}"
        etag = client.complete_multipart_upload(
            settings.MINIO_BUCKET_NAME,
            file_name,
            file_obj.file.upload_id
        )
        return file_name, file_url, etag, len(parts), parts, None # No checksum for multipart

    # Handle regular file upload
    else:
        result = client.put_object(
            settings.MINIO_BUCKET_NAME,
            file_name,
            file_obj,
            length=file_size,
            content_type=content_type
        )
        file_url = f"{settings.MINIO_ACCESS_URL}/{file_name}"
        return file_name, file_url, result.etag, 1, [], result.checksum_sha256

def minio_download(file_metadata, use_cache=False):
    """Downloads file from MinIO."""
    client = minio_storage()

    try:
        response = client.get_object(
            settings.MINIO_BUCKET_NAME,
            file_metadata.file_name,
        )
        file_data = response.read()
        file_size = response.length
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        return file_data, file_size, content_type

    except minio.error.S3Error as e:
        print(f"Error during the download: {e}")
        return None, 0, ""
    finally:
        if 'response' in locals():
            response.close()
            response.release_conn()

def minio_remove(file_name):
    """Remove a file from MinIO."""
    client = minio_storage()
    try:
        client.remove_object(settings.MINIO_BUCKET_NAME, file_name)
    except minio.error.S3Error as e:
        print(f"Error deleting file: {e}")

def get_presigned_url(file_name, expires_in=3600):
    """Generate a presigned URL for a given file."""
    client = minio_storage()
    try:
        url = client.presigned_get_object(
            settings.MINIO_BUCKET_NAME,
            file_name,
            expires=timedelta(seconds=expires_in)
        )
        return url
    except minio.error.S3Error as e:
        print(f"Error generating presigned URL: {e}")
        return None
