"""
File statistics and node performance monitoring.
This module tracks performance metrics for MinIO nodes.
"""

import logging
import math
import threading
import time

from django.core.cache import cache

from .node import node_manager

logger = logging.getLogger(__name__)

# Constants for node stats
NODE_STATS_PREFIX = "node_stats_"
NODE_STATS_TIMEOUT = 86400  # 24 hours cache for node statistics


class NodeStatistics:
    """Class to manage node performance statistics"""

    @staticmethod
    def get_node_stats(node_endpoint):
        """Get statistics for a specific node"""
        cache_key = f"{NODE_STATS_PREFIX}{node_endpoint}"
        stats = cache.get(
            cache_key,
            {
                "download_count": 0,
                "total_download_time": 0,
                "avg_download_time": 0,
                "success_rate": 100.0,
                "failure_count": 0,
                "last_failure": None,
            },
        )
        return stats

    @staticmethod
    def update_node_stats(node_endpoint, download_time=None, success=True):
        """Update statistics for a node after a download attempt"""
        cache_key = f"{NODE_STATS_PREFIX}{node_endpoint}"
        stats = NodeStatistics.get_node_stats(node_endpoint)

        if success and download_time is not None:
            stats["download_count"] += 1
            stats["total_download_time"] += download_time
            stats["avg_download_time"] = (
                stats["total_download_time"] / stats["download_count"]
            )
        elif not success:
            stats["failure_count"] += 1
            stats["last_failure"] = time.time()

        # Calculate success rate
        total_attempts = stats["download_count"] + stats["failure_count"]
        if total_attempts > 0:
            stats["success_rate"] = (stats["download_count"] / total_attempts) * 100

        # Update cache
        cache.set(cache_key, stats, NODE_STATS_TIMEOUT)
        return stats

    @staticmethod
    def track_download(node, file_size):
        """
        Track a download operation for a node.
        This updates the node's load factor based on recent performance.
        """
        if not node:
            return

        # Get current stats
        stats = NodeStatistics.get_node_stats(node.endpoint)

        # Calculate a load factor based on performance metrics
        # Lower is better - factors in response time and failure rate
        load_factor = 1.0

        if stats["download_count"] > 0:
            # Response time factor (normalized by file size)
            normalized_time = stats["avg_download_time"] / max(
                1, file_size / (1024 * 1024)
            )
            time_factor = min(1.0, normalized_time / 5.0)  # Cap at 1.0

            # Success rate factor
            success_factor = (100 - stats["success_rate"]) / 100

            # Combine factors
            load_factor = 0.7 * time_factor + 0.3 * success_factor

        # Update node's load value (thread-safe)
        with threading.Lock():
            node.load = load_factor

        logger.info(f"Updated node {node.endpoint} load to {load_factor:.4f}")


def monitor_nodes_health():
    """Periodically check and update health status of all nodes"""
    active_nodes = []

    for node in node_manager.nodes:
        is_healthy = node.check_health()
        if is_healthy:
            active_nodes.append(node)
        else:
            # Mark node as having high load if unhealthy
            with threading.Lock():
                node.load = 0.95

    # Log health status
    total_nodes = len(node_manager.nodes)
    total_active_nodes = len(active_nodes)
    logger.info(f"Node health check: {total_active_nodes}/{total_nodes} nodes active")

    return active_nodes, total_nodes


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])
