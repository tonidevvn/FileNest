# monitoring/management/commands/check_node_health.py
from django.core.management.base import BaseCommand
from core.minio.filestat import monitor_nodes_health

class Command(BaseCommand):
    help = 'Checks the health status of MinIO nodes'

    def handle(self, *args, **options):
        active_nodes, total_nodes = monitor_nodes_health()
        self.stdout.write(self.style.SUCCESS(f'Successfully checked node health: {active_nodes}/{total_nodes} active nodes'))
