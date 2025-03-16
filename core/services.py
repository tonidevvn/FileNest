"""Service layer for file operations."""

from typing import Dict, List, Optional, Tuple, Union

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse

from core.minio.node import node_manager
from core.minio.storage import (
    minio_remove,
    minio_upload,
)

from .models import FileChunk, FileMetadata


class FileService:
    """Service for handling file operations."""

    @staticmethod
    def validate_file(file_obj) -> List[str]:
        """Validate file size and name length."""
        MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
        MAX_FILENAME_LENGTH = 128
        errors = []

        if len(file_obj.name) > MAX_FILENAME_LENGTH:
            errors.append(
                f"File name exceeds {MAX_FILENAME_LENGTH} characters."
            )

        if file_obj.size > MAX_FILE_SIZE:
            errors.append(
                f"File size exceeds {MAX_FILE_SIZE / (1024 * 1024)}MB limit."
            )

        return errors

    @classmethod
    def upload_file(cls, file_obj, user: User) -> Tuple[FileMetadata, List[FileChunk]]:
        """Handle file upload and create metadata records."""
        # Validate file
        errors = cls.validate_file(file_obj)
        if errors:
            raise ValueError(errors[0])

        # Upload to MinIO
        file_name, file_url, etag, chunk_count, chunk_parts, checksum, is_valid = minio_upload(
            file_obj
        )

        if not is_valid:
            minio_remove(file_name)
            raise ValueError('Integrity check failed! Please try again.')
        else:
            # Create metadata record
            file_metadata = FileMetadata.objects.create(
                file_name=file_name,
                file_url=file_url,
                file_size=file_obj.size,
                etag=etag,
                location=settings.MINIO_BUCKET_NAME,
                uploaded_by=user,
                total_chunks=chunk_count,
                content_type=file_obj.content_type,
                checksum=checksum,
            )

            chunks = []
            if chunk_count > 1:
                for i, chunk_part in enumerate(chunk_parts):
                    chunk = FileChunk.objects.create(
                        file_metadata=file_metadata,
                        chunk_index=i,
                        chunk_file=chunk_part.part_number,
                        chunk_size=chunk_part.size,
                        etag=chunk_part.etag,
                    )
                    chunks.append(chunk)

            return file_metadata, chunks

    @staticmethod
    def delete_file(file_id: str, user: User) -> None:
        """Delete file and related chunks."""
        file_obj = FileMetadata.objects.get(id=file_id)

        if file_obj.uploaded_by != user and not user.is_staff:
            raise PermissionDenied("Unauthorized access")

        chunks = FileChunk.objects.filter(file_metadata=file_obj)
        for chunk in chunks:
            minio_remove(chunk.chunk_file)
            chunk.delete()

        if file_obj.file_name:
            minio_remove(file_obj.file_name)
            file_obj.delete()

    @staticmethod
    def get_file_details(file_id: str, user: User) -> FileMetadata:
        """Get file details with permission check."""
        file_obj = FileMetadata.objects.get(id=file_id)
        if file_obj.uploaded_by != user and not user.is_staff:
            raise PermissionDenied("Unauthorized access")
        return file_obj

    @staticmethod
    def list_files(
        user: User, page: int = 1, per_page: int = 20
    ) -> Tuple[List[FileMetadata], int]:
        """List files with pagination."""
        uploads_list = (
            FileMetadata.objects.select_related("uploaded_by").all()
            if user.is_staff
            else FileMetadata.objects.select_related("uploaded_by").filter(
                uploaded_by=user
            )
        )

        paginator = Paginator(uploads_list, per_page)
        page_obj = paginator.get_page(page)
        total = uploads_list.count()

        return page_obj, total

    @staticmethod
    def download_file(file_id: str, user: User) -> Union[HttpResponse, str]:
        """Download file from the least loaded node, returning a presigned URL."""
        file_obj = FileMetadata.objects.get(id=file_id)
        if file_obj.uploaded_by != user and not user.is_staff:
            raise PermissionDenied("Unauthorized access")

        cache_key = f"presigned_url_{file_id}"
        presigned_url = cache.get(cache_key)

        if presigned_url:
            try:
                response = requests.head(presigned_url)
                if response.status_code == 200:
                    return presigned_url
            except requests.exceptions.RequestException:
                pass

        # Get the least loaded node
        node = node_manager.get_least_loaded_node()
        if not node:
            raise Exception("No active MinIO nodes available.")

        # Generate presigned URL from the least loaded node's client
        presigned_url = node.client.presigned_get_object(
            node.bucket_name, file_obj.file_name
        )
        cache.set(cache_key, presigned_url, 3600)  # Cache for 1 hour

        return presigned_url

    @staticmethod
    def preview_urls(file_id: str, user: User) -> Union[HttpResponse, Dict]:
        """Download file from the least loaded node, returning a presigned URL."""
        file_obj = FileMetadata.objects.get(id=file_id)
        if file_obj.uploaded_by != user and not user.is_staff:
            raise PermissionDenied("Unauthorized access")

        presigned_urls = {}

        for node in node_manager.get_all_nodes():
            # Generate presigned URL from the least loaded node's client
            presigned_url = node.client.presigned_get_object(
                node.bucket_name, file_obj.file_name
            )
            presigned_urls[node] = presigned_url

        return presigned_urls
