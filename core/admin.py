"""Admin interface for core models."""
from django.contrib import admin
from .models import FileMetadata, FileChunk

@admin.register(FileMetadata)
class FileMetadataAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'uploaded_by', 'file_size', 'content_type', 'uploaded_at')
    list_filter = ('uploaded_by', 'content_type', 'uploaded_at')
    search_fields = ('file_name', 'uploaded_by__username')
    readonly_fields = ('id', 'uploaded_at', 'etag', 'checksum')
    date_hierarchy = 'uploaded_at'

@admin.register(FileChunk)
class FileChunkAdmin(admin.ModelAdmin):
    list_display = ('file_metadata', 'chunk_index', 'chunk_size', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('file_metadata__file_name',)
    readonly_fields = ('id', 'uploaded_at', 'etag')
