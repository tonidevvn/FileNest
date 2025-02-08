import os

from django.db import models
import uuid
from django.contrib.auth.models import User
from helpers.cloudflare.storages import MediaFileStorage
from helpers.storages.filestat import convert_size

def image_file_upload_handler(instance, filename):
    """Generates a unique file path using UUID."""
    return f"{instance.file_key}-{filename}"

class FileMetadata(models.Model):
    file = models.FileField(storage=MediaFileStorage(), null=True, blank=True, upload_to=image_file_upload_handler)
    file_key = models.CharField(
        max_length=36,
        unique=True,
        default=uuid.uuid1
    )  # Unique identifier for cloud storage
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def file_size(self):
        try:
            filesize = self.file.size
        except OSError:
            filesize = 0
        return convert_size(filesize)

    def __str__(self):
        return f"File {self.file.name} size of {self.file.size} bytes uploaded by {self.uploaded_by.username} at {self.uploaded_at}"

    def save(self, *args, **kwargs):
        """Ensure file size and file_key are set before saving."""
        if not self.file_key:
            self.file_key = str(uuid.uuid1())  # Ensure file_key is generated
        super().save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        """Delete file from cloud storage before removing the record."""
        if self.file:
            self.file.delete(save=False) # Remove file from cloud storage
        super().delete(*args, **kwargs)  # Delete database record