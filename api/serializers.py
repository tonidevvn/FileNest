from rest_framework import serializers
from django.contrib.auth.models import User
from upload.models import FileMetadata

class UserSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = User
        fields = ['id', 'username', 'password', 'email']

class FileMetadataSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = FileMetadata
        fields = ['id', 'file_name', 'file_url', 'file_size', 'content_type', 'etag', 
                 'location', 'total_chunks', 'checksum', 'uploaded_by', 'uploaded_at']

    def get_uploaded_by(self, obj):
        """Return the owner of the file."""
        return obj.uploaded_by.username if obj.uploaded_by else 'Guest'
