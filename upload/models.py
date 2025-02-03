from django.db import models
from helpers.cloudflare.storages import MediaFileStorage

class Upload(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(storage=MediaFileStorage(), null=True, blank=True)