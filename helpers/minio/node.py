from django.conf import settings
from minio import Minio

nodes = []


class Node:
    def __init__(
        self,
        endpoint,
        access_key,
        secret_key,
        secure,
        bucket_name,
        latitude,
        longitude,
        load,
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.bucket_name = bucket_name
        self.latitude = latitude
        self.longitude = longitude
        self.load = load
        self.access_url = f"{endpoint}/{bucket_name}"
        self.client = Minio(
            endpoint, access_key=access_key, secret_key=secret_key, secure=secure
        )

    def check_health(self):
        try:
            self.client.bucket_exists(self.bucket_name)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False


class NodeManager:
    def __init__(self):
        self.nodes = []
        # Initialize MinIO nodes
        for node in settings.MINIO_NODES:
            self.nodes.append(Node(**node))

    def get_active_nodes(self):
        return [node for node in self.nodes if node.check_health()]

    def get_nearest_node(self, latitude, longitude) -> Node:
        active_nodes = self.get_active_nodes()
        if not active_nodes:
            return None
        return min(
            active_nodes,
            key=lambda node: abs(node.latitude - latitude)
            + abs(node.longitude - longitude),
        )

    def get_least_loaded_node(self) -> Node:
        active_nodes = self.get_active_nodes()
        if not active_nodes:
            return None
        return min(active_nodes, key=lambda node: node.load)


node_manager = NodeManager()
