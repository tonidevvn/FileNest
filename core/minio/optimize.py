"""
Optimization utilities for MinIO file retrieval.
This module provides functions for optimized node selection and file caching.
"""

import logging

from django.conf import settings
from django.core.cache import cache

from .node import node_manager

# Get cache settings from Django settings or use defaults
FILE_CACHE_TIMEOUT = getattr(settings, "FILE_CACHE_TIMEOUT", 3600)
FILE_CACHE_PREFIX = getattr(settings, "FILE_CACHE_PREFIX", "file_cache_")
MAX_CACHED_FILE_SIZE = getattr(settings, "MAX_CACHED_FILE_SIZE", 5 * 1024 * 1024)

logger = logging.getLogger(__name__)


def get_optimal_node(user_lat=None, user_lon=None):
    """
    Get the optimal MinIO node based on user location or load.

    Args:
        user_lat: User's latitude
        user_lon: User's longitude

    Returns:
        The selected MinIO node
    """
    if user_lat is not None and user_lon is not None:
        # Use nearest node based on user location
        nearest_node = node_manager.get_nearest_node(user_lat, user_lon)
        if nearest_node and nearest_node.check_health():
            logger.info(f"Selected node based on location: {nearest_node.endpoint}")
            return nearest_node

    # Use least loaded node as fallback
    least_loaded = node_manager.get_least_loaded_node()
    if least_loaded and least_loaded.check_health():
        logger.info(f"Selected node based on load: {least_loaded.endpoint}")
        return least_loaded

    # Return default node if all else fails
    default_node = (
        node_manager.get_active_nodes()[0] if node_manager.get_active_nodes() else None
    )
    logger.info(
        f"Using default node: {default_node.endpoint if default_node else 'None'}"
    )
    return default_node


def get_cached_file(file_id):
    """
    Get file from cache if available.

    Args:
        file_id: ID of the file to retrieve from cache

    Returns:
        File data if found in cache, None otherwise
    """
    cache_key = f"{FILE_CACHE_PREFIX}{file_id}"
    cached_file = cache.get(cache_key)
    if cached_file:
        logger.info(f"Cache hit for file ID: {file_id}")
    return cached_file


def cache_file(file_id, file_data):
    """
    Cache file data if it's not too large.

    Args:
        file_id: ID of the file to cache
        file_data: The file data to cache

    Returns:
        True if cached, False otherwise
    """
    if len(file_data) <= MAX_CACHED_FILE_SIZE:
        cache_key = f"{FILE_CACHE_PREFIX}{file_id}"
        cache.set(cache_key, file_data, FILE_CACHE_TIMEOUT)
        logger.info(f"Cached file ID: {file_id}, size: {len(file_data)}")
        return True

    logger.info(f"File too large to cache, ID: {file_id}, size: {len(file_data)}")
    return False


def invalidate_cache(file_id):
    """
    Remove a file from cache.

    Args:
        file_id: ID of the file to remove from cache
    """
    cache_key = f"{FILE_CACHE_PREFIX}{file_id}"
    cache.delete(cache_key)
    logger.info(f"Invalidated cache for file ID: {file_id}")
