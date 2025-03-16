import hashlib
import io
import os
from datetime import timedelta

import minio
from django.conf import settings
from minio.api import Part

from core.minio.node import node_manager


def minio_storage():
    """Return MinIO client from the least loaded node."""
    node = node_manager.get_least_loaded_node()
    if not node:
        print("No active MinIO nodes available.")
        return None  # Or raise an exception if you prefer

    return node.client


def minio_upload(file_obj):
    """Upload a file to MinIO, handling both single and multipart uploads."""
    client = minio_storage()
    file_name = file_obj.name
    file_size = file_obj.size
    content_type = file_obj.content_type

    # Minimum part size for multipart uploads (5MB as per S3 specs)
    MIN_PART_SIZE = 5 * 1024 * 1024

    if not client.bucket_exists(settings.MINIO_BUCKET_NAME):
        client.make_bucket(settings.MINIO_BUCKET_NAME)

    try:
        # For very small files, always use single-part upload
        if file_size < MIN_PART_SIZE:
            # Single part upload for small files
            file_hash = hashlib.md5()
            file_hash.update(file_obj.read())
            calculated_checksum = file_hash.hexdigest()

            # Reset file pointer to beginning
            file_obj.seek(0)

            result = client.put_object(
                settings.MINIO_BUCKET_NAME,
                file_name,
                file_obj,
                length=file_size,
                content_type=content_type,
            )
            file_url = f"{settings.MINIO_ACCESS_URL}/{file_name}"

            # Compare calculated checksum with MinIO ETag
            is_valid = result.etag.strip('"') == calculated_checksum

            return (
                file_name,
                file_url,
                result.etag,
                1,
                [],
                calculated_checksum,
                is_valid,
            )

        elif hasattr(file_obj, "chunks"):  # Handle multipart uploads for larger files
            # Reset file pointer to beginning
            file_obj.seek(0)

            upload_id = client._create_multipart_upload(
                settings.MINIO_BUCKET_NAME, file_name, {}
            )
            parts = []
            part_num = 1
            print(
                f"Multipart upload started for: {file_name}, upload_id: {upload_id}, file_size: {file_size}"
            )

            # Buffer to accumulate chunks until minimum part size
            buffer = bytearray()

            # Process chunks ensuring each part meets minimum size
            md5_parts = []  # Store MD5 hashes of parts
            for chunk in file_obj.chunks():
                buffer.extend(chunk)

                # Upload part when buffer size exceeds minimum part size
                # or it's the last part and buffer has content
                if len(buffer) >= MIN_PART_SIZE or (
                    file_obj.file.tell() == file_size and buffer
                ):
                    md5_parts.append(hashlib.md5(buffer))

                    part = client._upload_part(
                        settings.MINIO_BUCKET_NAME,
                        file_name,
                        buffer,
                        {},
                        upload_id,
                        part_num,
                    )
                    parts.append(
                        Part(part_number=part_num, etag=part, size=len(buffer))
                    )
                    print(f"  Part {part_num} uploaded, part size: {len(buffer)}")
                    part_num += 1
                    buffer = bytearray()  # Reset buffer

            result = client._complete_multipart_upload(
                settings.MINIO_BUCKET_NAME, file_name, upload_id, parts
            )
            file_url = f"{settings.MINIO_ACCESS_URL}/{file_name}"
            print(
                f"Multipart upload completed for: {file_name}, total parts: {len(parts)}"
            )

            # Compute MD5 for the whole file using ETag-style hashing
            digests = b"".join(m.digest() for m in md5_parts)
            digests_md5 = hashlib.md5(digests)
            multipart_md5 = "{}-{}".format(digests_md5.hexdigest(), len(md5_parts))

            # Compare calculated checksum with MinIO ETag
            is_valid = result.etag.strip('"') == multipart_md5

            return (
                file_name,
                file_url,
                result.etag,
                len(parts),
                parts,
                multipart_md5,
                is_valid,
            )

        else:  # Fallback for objects without chunks method
            # Calculate SHA256 checksum
            file_hash = hashlib.md5()
            file_data = file_obj.read()
            file_hash.update(file_data)
            calculated_checksum = file_hash.hexdigest()

            # Reset file pointer to beginning
            file_obj.seek(0)

            result = client.put_object(
                settings.MINIO_BUCKET_NAME,
                file_name,
                file_obj,
                length=file_size,
                content_type=content_type,
            )
            file_url = f"{settings.MINIO_ACCESS_URL}/{file_name}"

            # Compare calculated checksum with MinIO ETag
            is_valid = result.etag.strip('"') == calculated_checksum

            return (
                file_name,
                file_url,
                result.etag,
                1,
                [],
                calculated_checksum,
                is_valid,
            )

    except minio.error.S3Error as e:
        error_message = f"-----------------MinIO upload failed: {e}"
        print(error_message)  # Consider using logging instead of print
        return (
            None,
            None,
            None,
            None,
            None,
            None,
            error_message,
        )  # Failure, return error


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
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        return file_data, file_size, content_type

    except minio.error.S3Error as e:
        print(f"Error during the download: {e}")
        return None, 0, ""
    finally:
        if "response" in locals():
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
    """Generate a presigned URL for a given file using the least loaded node."""
    node = node_manager.get_least_loaded_node()
    if not node:
        print(
            "No active MinIO nodes available."
        )  # Log this instead of raising exception for now
        return None

    client = node.client  # Use client from the least loaded node
    try:
        url = client.presigned_get_object(
            node.bucket_name, file_name, expires=timedelta(seconds=expires_in)
        )
        return url
    except minio.error.S3Error as e:
        print(f"Error generating presigned URL: {e} from node: {node.name}")
        return None
