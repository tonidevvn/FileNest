"""Core models for FileNest."""

import uuid

from django.contrib.auth.models import User
from django.db import models

from core.minio.filestat import convert_size


class FileMetadata(models.Model):
    """Model for storing file metadata and location information."""

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    file_name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=255, null=True, blank=True)
    etag = models.CharField(max_length=255, null=True, blank=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="core_files"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    total_chunks = models.IntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["-uploaded_at"]),
            models.Index(fields=["uploaded_by", "-uploaded_at"]),
        ]

    def __str__(self):
        return f"File {self.file_name} size of {convert_size(self.file_size)} bytes uploaded by {self.uploaded_by.username}"

    @property
    def is_image(self):
        """Check if the file is an image based on its extension."""
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        return any(self.file_name.lower().endswith(ext) for ext in image_extensions)

    def get_chunks_count(self):
        """Return the number of chunks for this file."""
        return self.chunks.count()

    def get_display_name(self):
        """Get the original file name without the UUID prefix."""
        parts = self.file_name.split("-", 1)
        return parts[1] if len(parts) > 1 else self.file_name


class FileChunk(models.Model):
    """Model for storing individual file chunks for large file uploads."""

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    file_metadata = models.ForeignKey(
        FileMetadata, on_delete=models.CASCADE, related_name="chunks"
    )
    chunk_index = models.IntegerField()
    chunk_file = models.CharField(max_length=255, null=True, blank=True)
    chunk_size = models.IntegerField(null=True, blank=True)
    etag = models.CharField(max_length=255, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chunk_index"]
        unique_together = ("file_metadata", "chunk_index")
        indexes = [
            models.Index(fields=["file_metadata", "chunk_index"]),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.file_metadata.file_name}"

    def get_size_display(self):
        """Return human-readable size."""
        return convert_size(self.chunk_size)
