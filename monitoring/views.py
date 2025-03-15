"""Views for monitoring file access and system activities."""
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render
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
