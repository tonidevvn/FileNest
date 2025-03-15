import requests
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
        region,
        load,
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.bucket_name = bucket_name
        self.load = load
        self.region = region
        self.endpoint = endpoint
        self.access_url = f"{endpoint}/{bucket_name}"

        # Initialize MinIO client with retry and proper pool_size
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            http_client=None,  # Use default client with automatic retries
        )
        print(f"Minio endpoint for client: {endpoint}")

    def check_health(self):
        try:
            self.client.bucket_exists(self.bucket_name)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def check_file_status(self, file_name):
        """Check if the file URL is accessible (status 200)."""
        try:
            url = f"http://{self.access_url}/{file_name}"
            response = requests.head(url, timeout=2)  # Use HEAD request for efficiency
            if response.status_code == 200:
                return "Available"
            else:
                return "Not found"
        except requests.RequestException:
            return "Not found"


class NodeManager:
    def __init__(self):
        self.nodes = []
        # Initialize MinIO nodes
        for node in settings.MINIO_NODES:
            self.nodes.append(Node(**node))

    def get_all_nodes(self):
        return [node for node in self.nodes]

    def get_active_nodes(self):
        return [node for node in self.nodes if node.check_health()]

    def get_least_loaded_node(self) -> Node:
        from core.minio.filestat import monitor_nodes_health  # Import here to avoid circular import

        monitor_nodes_health()  # Update node loads before selecting

        active_nodes = self.get_active_nodes()
        if not active_nodes:
            return None
        return min(active_nodes, key=lambda node: node.load)


node_manager = NodeManager()
