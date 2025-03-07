from rest_framework import serializers
from django.contrib.auth.models import User
from upload.models import FileMetadata

class UserSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = User
        fields = ['id', 'username', 'password', 'email']

class FileMetadataSerializer(serializers.ModelSerializer):
    file_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()
    etag = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    total_chunks = serializers.SerializerMethodField()
    checksum = serializers.SerializerMethodField()
    uploaded_by = serializers.SerializerMethodField()
    uploaded_at = serializers.SerializerMethodField()

    class Meta(object):
        model = FileMetadata
        fields = ['id', 'file_name', 'file_url', 'file_size', 'content_type', 'etag', 'location', 'total_chunks', 'checksum', 'uploaded_by', 'uploaded_at']

    def get_file_name(self, obj):
        return obj.file_name

    def get_file_url(self, obj):
        return obj.file_url

    def get_file_size(self, obj):
        return obj.file_size

    def get_content_type(self, obj):
        return obj.content_type

    def get_etag(self, obj):
        return obj.etag

    def get_location(self, obj):
        return obj.location

    def get_total_chunks(self, obj):
        return obj.total_chunks

    def get_checksum(self, obj):
        return obj.checksum

    def get_uploaded_at(self, obj):
        return obj.uploaded_at

    def get_uploaded_by(self, obj):
        """Return the owner of the file."""
        if obj.uploaded_by:
            return obj.uploaded_by.username
        return 'Guest'
