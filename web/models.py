"""Models for upload app."""
# Models have been moved to core app
from core.models import FileMetadata, FileChunk  # noqa

# Keep these imports for backward compatibility
__all__ = ['FileMetadata', 'FileChunk']
