from django.db import models
import uuid
from django.contrib.auth.models import User
from helpers.cloudflare.storages import MediaFileStorage

def image_file_upload_handler(instance, filename):
    uid = uuid.uuid1()
    return f"{uid}-{filename}"

class FileMetadata(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(storage=MediaFileStorage(), null=True, blank=True, upload_to=image_file_upload_handler)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"File {self.file.name} uploaded by {self.uploaded_by.username} at {self.uploaded_at}"
