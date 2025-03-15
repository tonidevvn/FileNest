"""API serializers for FileNest."""
from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import FileMetadata

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class FileMetadataSerializer(serializers.ModelSerializer):
    """Serializer for FileMetadata model."""
    uploaded_by = UserSerializer(read_only=True)
    display_name = serializers.CharField(source='get_display_name', read_only=True)

    class Meta:
        model = FileMetadata
        fields = (
            'id', 'file_name', 'file_url', 'file_size',
            'content_type', 'uploaded_at', 'uploaded_by',
            'total_chunks', 'etag', 'location', 'display_name'
        )
