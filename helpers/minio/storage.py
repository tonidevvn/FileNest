from io import BytesIO
from django.utils.text import get_valid_filename
from minio import Minio
from django.conf import settings
import uuid

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
    chunk_size = 5 * 1024 * 1024  # 5MB in bytes
    chunk_count = (file_size + chunk_size - 1) // chunk_size  # Ceiling division
    file_name = f"{uuid.uuid4()}-{clean_name}"
    file_data = uploaded_file.read()  # Returns bytes
    result = minio_client.put_object(
        settings.MINIO_BUCKET_NAME,
        file_name,
        BytesIO(file_data),
        part_size= chunk_size,  # 5MB in bytes
        length=file_size
    )
    file_url = f"{settings.MINIO_ACCESS_URL}/{file_name}"
    if not settings.MINIO_SECURE:
        file_url = "http://" + file_url
    else:
        file_url = "https://" + file_url
    etag = result.etag

    return file_name, file_url, etag, chunk_count

def minio_remove(file_name):
    minio_client.remove_object(
        settings.MINIO_BUCKET_NAME,
        file_name
    )