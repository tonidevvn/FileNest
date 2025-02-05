import os

from django.db import models
import uuid
from django.contrib.auth.models import User
from helpers.cloudflare.storages import MediaFileStorage
from helpers.storages.filestat import convert_size

def image_file_upload_handler(instance, filename):
    uid = uuid.uuid1()
    return f"{uid}-{filename}"

class FileMetadata(models.Model):
    file = models.FileField(storage=MediaFileStorage(), null=True, blank=True, upload_to=image_file_upload_handler)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File {self.file.name} size of {self.file.size} bytes uploaded by {self.uploaded_by.username} at {self.uploaded_at}"

    @property
    def file_size(self):
        return convert_size(self.file.size)