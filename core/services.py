"""Service layer for file operations."""

from typing import Dict, List, Optional, Tuple, Union

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse

from core.minio.storage import (
    get_presigned_url,
    minio_download,
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
                f"File name '{file_obj.name}' exceeds {MAX_FILENAME_LENGTH} characters."
            )

        if file_obj.size > MAX_FILE_SIZE:
            errors.append(
                f"File '{file_obj.name}' exceeds {MAX_FILE_SIZE / (1024 * 1024)}MB limit."
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
        file_name, file_url, etag, chunk_count, chunk_parts, checksum = minio_upload(
            file_obj
        )

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
        """Download file with permission check, returning a presigned URL."""
        file_obj = FileMetadata.objects.get(id=file_id)
        if file_obj.uploaded_by != user and not user.is_staff:
            raise PermissionDenied("Unauthorized access")

        # Generate presigned URL
        presigned_url = get_presigned_url(file_obj.file_name)

        if presigned_url:
            return presigned_url
        else:
            # Handle error (e.g., MinIO not reachable)
            raise Exception("Could not generate presigned URL")
