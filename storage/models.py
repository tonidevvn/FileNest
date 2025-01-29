from django.db import models

class StorageNode(models.Model):
    """Represents a distributed storage node."""
    name = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField(unique=True)
    storage_capacity = models.FloatField()  # In GB
    available_space = models.FloatField()
    is_active = models.BooleanField(default=True)
    last_heartbeat = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class FileMetadata(models.Model):
    """Stores metadata for each uploaded file."""
    file_name = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, unique=True)  # SHA-256 Hash
    size = models.FloatField()  # In MB
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

class FileChunk(models.Model):
    """Represents file chunks distributed across storage nodes."""
    file = models.ForeignKey(FileMetadata, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.IntegerField()
    chunk_hash = models.CharField(max_length=64, unique=True)
    size = models.FloatField()
    nodes = models.ManyToManyField(StorageNode, related_name="chunks")

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.file.file_name}"
