from io import BytesIO
from django.utils.text import get_valid_filename
from minio import Minio
from django.conf import settings
import uuid

from minio.commonconfig import ComposeSource

# Initialize MinIO client
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)

def minio_upload(uploaded_file):
    # Ensure bucket exists
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
        minio_client.make_bucket(settings.MINIO_BUCKET_NAME)

    clean_name = get_valid_filename(uploaded_file.name)  # Sanitize file name
    file_size = uploaded_file.size
    chunk_size = 5 * 1024 * 1024 + 2  # 5MB in bytes
    chunk_count = (file_size + chunk_size - 1) // chunk_size  # Ceiling division
    file_name = f"{uuid.uuid4()}-{clean_name}"
    chunk_parts = []  # List to store uploaded chunk paths

    if chunk_count == 1:
        file_data = uploaded_file.read()  # Returns bytes
        file_obj = minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            file_name,
            BytesIO(file_data),
            part_size= chunk_size,  # 5MB in bytes
            length=file_size
        )
    else:
        chunk_sources = []
        # Iterate over chunks
        for i in range(chunk_count):
            # Read a chunk
            if i < chunk_count - 1:
                chunk_data = uploaded_file.read(chunk_size)  # Read exactly 5MB
            else:
                chunk_data = uploaded_file.read()  # Read remaining bytes (last chunk)
            if not chunk_data:
                break

            # Wrap chunk in BinaryIO
            chunk_stream = BytesIO(chunk_data)
            chunk_name = f"{uploaded_file.name}.part.{i}"
            chunk_size = len(chunk_data)

            # Upload chunk to MinIO
            chunk_obj = minio_client.put_object(
                settings.MINIO_BUCKET_NAME,
                chunk_name,
                chunk_stream,
                length=chunk_size
            )
            chunk_sources.append(ComposeSource(settings.MINIO_BUCKET_NAME, chunk_name, offset=i))
            chunk_parts.append({"name": chunk_name, "etag": chunk_obj.etag, "size": chunk_size})

        # Merge chunks into a single object
        file_obj = minio_client.compose_object(
            settings.MINIO_BUCKET_NAME,
            file_name,
            sources=chunk_sources
        )

    file_url = f"{settings.MINIO_ACCESS_URL}/{file_name}"
    if not settings.MINIO_SECURE:
        file_url = "http://" + file_url
    else:
        file_url = "https://" + file_url
    etag = file_obj.etag

    return file_name, file_url, etag, chunk_count, chunk_parts

def minio_remove(file_name):
    minio_client.remove_object(
        settings.MINIO_BUCKET_NAME,
        file_name
    )