from rest_framework import serializers
from django.contrib.auth.models import User
from upload.models import FileMetadata

class UserSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = User
        fields = ['id', 'username', 'password', 'email']

class FileMetadataSerializer(serializers.ModelSerializer):
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    uploaded_by = serializers.SerializerMethodField()

    class Meta(object):
        model = FileMetadata
        fields = ['id', 'etag', 'file_name', 'uploaded_by', 'uploaded_at', 'file_size', 'file_url']

    def get_file_name(self, obj):
        """Return the name of the file."""
        return obj.file_name

    def get_file_url(self, obj):
        """Return the full URL of the file (works for S3 and local storage)."""
        return obj.file_url

    def get_file_size(self, obj):
        """Return the full URL of the file (works for S3 and local storage)."""
        return obj.file_size

    def get_uploaded_by(self, obj):
        """Return the owner of the file."""
        if obj.uploaded_by:
            return obj.uploaded_by.username
        return 0
