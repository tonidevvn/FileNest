from django.db import models
import uuid
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from helpers.cloudflare.storages import MediaFileStorage
from helpers.storages.chunks import handle_r2_multipart_upload, handle_local_chunking
from helpers.storages.filestat import convert_size
from django.conf import settings

def image_file_upload_handler(instance, filename):
    """Generates a unique file path using UUID."""
    return f"{instance.file_key}-{filename}"

# Define a local storage instance
local_storage = FileSystemStorage(location=settings.LOCAL_STORAGE_URL)

class FileMetadata(models.Model):
    STORAGE_CHOICES_LOCAL = 'local'
    STORAGE_CHOICES_CLOUD = 'cloud'

    STORAGE_CHOICES = [
        (STORAGE_CHOICES_LOCAL, 'Local Storage'),
        (STORAGE_CHOICES_CLOUD, 'Cloud Storage'),
    ]

    file_cloud = models.FileField(storage= MediaFileStorage(), null=True, blank=True, upload_to=image_file_upload_handler)
    file_localhost = models.FileField(storage= local_storage, null=True, blank=True, upload_to=image_file_upload_handler)
    file_key = models.CharField(
        max_length=36,
        unique=True,
        default=uuid.uuid1
    )  # Unique identifier for cloud storage
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    storage_type = models.CharField(
        max_length=10, choices=STORAGE_CHOICES, default='cloud'
    )  # Determines whether to use local or cloud storage
    is_chunked = models.BooleanField(default=False)
    total_chunks = models.IntegerField(default=0)


    @property
    def file_size_str(self):
        filesize = 0
        """Returns the correct file size based on storage type."""
        if self.storage_type == FileMetadata.STORAGE_CHOICES_CLOUD and self.file_cloud:
            filesize = self.file_cloud.size
        elif self.storage_type == FileMetadata.STORAGE_CHOICES_LOCAL and self.file_localhost:
            filesize = self.file_localhost.size
        return convert_size(filesize)

    @property
    def file_size(self):
        filesize = 0
        """Returns the correct file size based on storage type."""
        if self.storage_type == FileMetadata.STORAGE_CHOICES_CLOUD and self.file_cloud:
            filesize = self.file_cloud.size
        elif self.storage_type == FileMetadata.STORAGE_CHOICES_LOCAL and self.file_localhost:
            filesize = self.file_localhost.size
        return filesize

    @property
    def file_url(self):
        """Returns the correct file URL based on storage type."""
        if self.storage_type == FileMetadata.STORAGE_CHOICES_CLOUD and self.file_cloud:
            return self.file_cloud.url
        elif self.storage_type == FileMetadata.STORAGE_CHOICES_LOCAL and self.file_localhost:
            return f"{settings.LOCAL_STORAGE_URL}{self.file_localhost.name}"  # Generate correct local file path
        return None

    @property
    def file_name(self):
        """Returns the correct file name based on storage type."""
        if self.storage_type == FileMetadata.STORAGE_CHOICES_CLOUD and self.file_cloud:
            return self.file_cloud.name
        elif self.storage_type == FileMetadata.STORAGE_CHOICES_LOCAL and self.file_localhost:
            return self.file_localhost.name
        return None

    def __str__(self):
        return f"File {self.file_name} size of {self.file_size_str} bytes uploaded by {self.uploaded_by.username} at {self.uploaded_at}"

    def save(self, *args, **kwargs):
        """Ensure file size and file_key are set before saving."""
        if not self.file_key:
            self.file_key = str(uuid.uuid1())  # Ensure file_key is generated

        super().save(*args, **kwargs)

        # Check if the file size exceeds 5MB
        if self.file_size > 5 * 1024 * 1024:  # 5MB in bytes
            if self.storage_type == 'cloud':
                self.is_chunked, self.total_chunks = handle_r2_multipart_upload(self.file_cloud, self.file_name)
            else:
                self.is_chunked, self.total_chunks = handle_local_chunking(self.file_localhost, self.file_name)
            super().save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        """Delete file from cloud storage before removing the record."""
        if self.storage_type == FileMetadata.STORAGE_CHOICES_CLOUD and self.file_cloud:
            self.file_cloud.delete(save=False) # Remove file from cloud storage
        elif self.storage_type == FileMetadata.STORAGE_CHOICES_LOCAL and self.file_localhost:
            self.file_localhost.delete(save=False)
        super().delete(*args, **kwargs)  # Delete database record

class FileChunk(models.Model):
    """Stores individual file chunks for a larger file."""
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    file_metadata = models.ForeignKey(FileMetadata, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    chunk_file_cloud = models.FileField(storage=MediaFileStorage(), null=True, blank=True)
    chunk_file_localhost = models.FileField(storage=local_storage, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('file_metadata', 'chunk_index')  # Prevent duplicate chunk uploads

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.file_metadata.file_key}"