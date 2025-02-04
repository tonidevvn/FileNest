from storages.backends.s3boto3 import S3Boto3Storage
import helpers.storages.mixins as mixins


class CloudStorage(S3Boto3Storage):
    pass


class StaticFileStorage(mixins.DefaultACLMixin, CloudStorage):
    """
    For staticfiles
    """

    location = "static"
    default_acl = "public-read"


class MediaFileStorage(mixins.DefaultACLMixin, CloudStorage):
    """
    For general uploads
    """

    location = "media"
    default_acl = "public-read"


class ProtectedMediaStorage(mixins.DefaultACLMixin, CloudStorage):
    """
    For user private uploads
    """

    location = "protected"
    default_acl = "private"
