from django.db import models
from django.contrib.auth.models import User
import uuid
from helpers.minio.filestat import convert_size


class FileMetadata(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    file_name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=255, null=True, blank=True)
    etag = models.CharField(max_length=255, null=True, blank=True)  # Stores MinIO ETag
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, null=True, blank=True)  # e.g., MinIO bucket path
    total_chunks = models.IntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True)  # For error checking

    def __str__(self):
        return f"File {self.file_name} size of {convert_size(self.file_size)} bytes uploaded by {self.uploaded_by.username} at {self.uploaded_at}"


class FileChunk(models.Model):
    """Stores individual file chunks for a larger file."""
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    file_metadata = models.ForeignKey(FileMetadata, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    chunk_file = models.CharField(max_length=255, null=True, blank=True)
    chunk_size = models.IntegerField(null=True, blank=True)
    etag = models.CharField(max_length=255, null=True, blank=True)  # Stores MinIO ETag
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('file_metadata', 'chunk_index')  # Prevent duplicate chunk uploads

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.file_metadata.etag}"