from django.contrib import admin
from .models import FileMetadata, FileChunk, StorageNode

@admin.register(FileMetadata)
class FileMetadataAdmin(admin.ModelAdmin):
    list_display = ("file_name", "file_hash", "total_chunks", "uploaded_at")
    search_fields = ("file_name", "file_hash")

@admin.register(FileChunk)
class FileChunkAdmin(admin.ModelAdmin):
    list_display = ("file", "chunk_index", "chunk_hash", "s3_key")
    search_fields = ("chunk_hash", "s3_key")

@admin.register(StorageNode)
class StorageNodeAdmin(admin.ModelAdmin):
    list_display = ("name", "ip_address", "storage_capacity", "available_space", "is_active")
    search_fields = ("name", "ip_address")
