"""Views for monitoring file access and system activities."""
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render

from core.minio.node import node_manager
from core.models import FileMetadata
from .models import FileAccessLog

def log_file_action(user, file_name, action, request):
    """Create a new file access log entry."""
    return FileAccessLog.objects.create(
        user=user,
        file_name=file_name,
        action=action,
        ip_address=request.META.get('REMOTE_ADDR', 'Unknown')
    )

@staff_member_required
def log_monitoring(request):
    """Display paginated file access logs."""
    logs = FileAccessLog.objects.select_related('user').order_by('-timestamp')
    
    # Filter by action if specified
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)

    # Filter by username if specified
    username = request.GET.get('username')
    if username:
        logs = logs.filter(user__username=username)

    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page', 1)
    logs_page = paginator.get_page(page_number)

    context = {
        'logs': logs_page,
        'action_choices': FileAccessLog.ACTION_CHOICES,
        'selected_action': action_filter,
        'username_filter': username,
    }
    
    return render(request, 'monitoring/logs.html', context)


@staff_member_required
def admin_dashboard(request):
    """Admin dashboard to monitor node status and file distribution."""
    nodes = node_manager.get_all_nodes()
    file_list = FileMetadata.objects.all()  # Fetch all files for distribution table - might need pagination later

    files_data = []
    for file_metadata in file_list:
        node_statuses = [node.check_file_status(file_metadata.file_name) for node in nodes]
        files_data.append({
            'file_name': file_metadata.file_name,
            'node_statuses': node_statuses,
        })


    context = {
        'nodes': nodes,
        'files': files_data,
    }
    return render(request, 'monitoring/admin_dashboard.html', context)
