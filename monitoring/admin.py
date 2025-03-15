"""Admin interface for monitoring models."""
from django.contrib import admin
from .models import FileAccessLog

@admin.register(FileAccessLog)
class FileAccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'file_name', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('file_name', 'user__username', 'ip_address')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
