# helpers.py

import os
import boto3
from django.conf import settings

CHUNK_SIZE = 5 * 1024 * 1024  # 5MB

def handle_local_chunking(file, file_name):
    # Remove the file extension from the file_name
    base_name, _ = os.path.splitext(file_name)
    # Create the chunk directory path without the file extension
    chunk_dir = os.path.join(settings.MEDIA_ROOT, 'lfs', base_name)
    os.makedirs(chunk_dir, exist_ok=True)
    chunk_index = 0

    for chunk in file.chunks(CHUNK_SIZE):
        chunk_filename = f'{file_name}_chunk_{chunk_index}'
        chunk_path = os.path.join(str(chunk_dir), chunk_filename)
        with open(chunk_path, 'wb') as chunk_file:
            chunk_file.write(chunk)
        chunk_index += 1

    return True, chunk_index  # is_chunked=True, total_chunks=chunk_index

def handle_r2_multipart_upload(file, file_name):
    session = boto3.session.Session()

    s3_client = session.client(
        's3',
        region_name=settings.AWS_S3_REGION_NAME,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    multipart_upload = s3_client.create_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=f"lfs/{file_name}",
    )

    parts = []
    part_number = 1

    for chunk in file.chunks(CHUNK_SIZE):
        response = s3_client.upload_part(
            Body=chunk,
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=f"lfs/{file_name}",
            PartNumber=part_number,
            UploadId=multipart_upload['UploadId'],
        )
        parts.append({'PartNumber': part_number, 'ETag': response['ETag']})
        part_number += 1

    s3_client.complete_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=f"lfs/{file_name}",
        UploadId=multipart_upload['UploadId'],
        MultipartUpload={'Parts': parts},
    )

    return True, part_number - 1  # is_chunked=True, total_chunks=part_number - 1
