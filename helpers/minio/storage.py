import hashlib
import logging
import time
import uuid
from io import BytesIO

from django.shortcuts import get_list_or_404
from django.utils.text import get_valid_filename
from minio.commonconfig import ComposeSource

from upload.models import FileChunk

from .filestat import NodeStatistics
from .node import node_manager
from .optimize import cache_file, get_cached_file, get_optimal_node, invalidate_cache

# Initialize MinIO client
# Get current geographical location
cur_lat = 37.0902
cur_lon = -95.7129
node = node_manager.get_nearest_node(cur_lat, cur_lon)
bucket_name = node.bucket_name
secured = node.secure
access_url = node.access_url
minio_client = node.client

# Set up logging
logger = logging.getLogger(__name__)


def minio_upload(uploaded_file):
    # Ensure bucket exists
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    clean_name = get_valid_filename(uploaded_file.name)  # Sanitize file name
    file_size = uploaded_file.size
    chunk_size = 5 * 1024 * 1024 + 2  # 5MB in bytes
    chunk_count = (file_size + chunk_size - 1) // chunk_size  # Ceiling division
    file_name = f"{uuid.uuid4()}-{clean_name}"
    chunk_parts = []  # List to store uploaded chunk paths
    chunk_sources = []
    hash_sha256 = hashlib.sha256()

    if chunk_count == 1:
        file_data = uploaded_file.read()  # Returns bytes
        hash_sha256.update(file_data)  # Compute checksum while reading
        file_obj = minio_client.put_object(
            bucket_name,
            file_name,
            BytesIO(file_data),
            part_size=chunk_size,  # 5MB in bytes
            length=file_size,
        )
    else:
        # Iterate over chunks
        for i in range(chunk_count):
            # Read a chunk
            if i < chunk_count - 1:
                chunk_data = uploaded_file.read(chunk_size)  # Read exactly 5MB
            else:
                chunk_data = uploaded_file.read()  # Read remaining bytes (last chunk)
            if not chunk_data:
                break

            # Wrap chunk in BinaryIO
            chunk_stream = BytesIO(chunk_data)
            chunk_name = f"{uploaded_file.name}.part.{i}"
            chunk_size = len(chunk_data)
            hash_sha256.update(chunk_data)  # Compute checksum while reading

            # Upload chunk to MinIO
            chunk_obj = minio_client.put_object(
                bucket_name, chunk_name, chunk_stream, length=chunk_size
            )
            chunk_sources.append(ComposeSource(bucket_name, chunk_name, offset=i))
            chunk_parts.append(
                {"name": chunk_name, "etag": chunk_obj.etag, "size": chunk_size}
            )

        # Merge chunks into a single object
        file_obj = minio_client.compose_object(
            bucket_name, file_name, sources=chunk_sources
        )

    file_url = f"{access_url}/{file_name}"
    if not secured:
        file_url = "http://" + file_url
    else:
        file_url = "https://" + file_url
    etag = file_obj.etag
    checksum = hash_sha256.hexdigest()

    return file_name, file_url, etag, chunk_count, chunk_parts, checksum


def minio_download(file_metadata, use_cache=True, user_lat=None, user_lon=None):
    """
    Download a file from MinIO storage with optimization.

    Args:
        file_metadata: The file metadata object
        use_cache: Whether to use cache for this file (default: True)
        user_lat: User's latitude for optimized node selection
        user_lon: User's longitude for optimized node selection
    """
    try:
        file_name = file_metadata.file_name
        file_size = file_metadata.file_size
        content_type = file_metadata.content_type or "application/octet-stream"

        # Check cache first if caching is enabled
        if use_cache:
            cached_file = get_cached_file(file_metadata.id)
            if cached_file:
                return BytesIO(cached_file), file_size, content_type

        # Get optimal node based on user location or load
        node = get_optimal_node(user_lat, user_lon)
        client = node.client if node else minio_client

        # Track download performance
        start_time = time.time()
        success = False

        try:
            # Get file from the selected node
            response = client.get_object(bucket_name, file_name)
            file_data = response.read()

            # Track successful download
            download_time = time.time() - start_time
            success = True

            # Update node statistics
            NodeStatistics.update_node_stats(node.endpoint, download_time, success=True)
            NodeStatistics.track_download(node, file_size)

            # Cache the file if caching is enabled
            if use_cache:
                cache_file(file_metadata.id, file_data)

            return BytesIO(file_data), file_size, content_type

        except Exception as node_error:
            # Track failed download
            NodeStatistics.update_node_stats(node.endpoint, success=False)
            logger.warning(f"Download from node {node.endpoint} failed: {node_error}")

            # Try with default client as fallback if we used a different node
            if client != minio_client:
                logger.info(f"Falling back to default node for file: {file_name}")
                response = minio_client.get_object(bucket_name, file_name)
                file_data = response.read()

                # Cache the file if caching is enabled
                if use_cache:
                    cache_file(file_metadata.id, file_data)

                return BytesIO(file_data), file_size, content_type
            else:
                raise node_error

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise e


def minio_remove(file_to_delete):
    try:
        file_name = file_to_delete.file_name

        minio_client.remove_object(bucket_name, file_name)

        chunks = get_list_or_404(FileChunk, file_metadata=file_to_delete)
        for chunk in chunks:
            minio_client.remove_object(bucket_name, chunk.chunk_file)

        # Remove main file from MinIO
        minio_client.remove_object(bucket_name, file_name)

        # Clear the file from cache
        invalidate_cache(file_to_delete.id)

    except Exception as e:
        logger.error(f"Error removing file: {e}")

    return {"message": "File and its chunks removed successfully."}
