import hashlib
import boto3
from django.conf import settings

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

def hash_chunk(chunk):
    """Generate SHA-256 hash for a chunk."""
    return hashlib.sha256(chunk).hexdigest()

def chunk_file(file, chunk_size=5 * 1024 * 1024):  # 5MB per chunk
    """Splits a file into chunks."""
    chunks = []
    index = 0
    while True:
        chunk_data = file.read(chunk_size)
        if not chunk_data:
            break
        chunk_hash = hash_chunk(chunk_data)
        chunks.append((index, chunk_data, chunk_hash))
        index += 1
    return chunks

def upload_chunk_to_s3(chunk_data, s3_key):
    """Uploads a chunk to AWS S3."""
    s3_client.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=s3_key,
        Body=chunk_data
    )
    return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
