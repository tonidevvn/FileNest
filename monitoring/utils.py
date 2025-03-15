from .models import FileAccessLog

def log_file_action(user, file_name, action, request):
    """Log file access and operations."""
    print(f"Logging action: {action} on {file_name} by {user}")

    log_entry = FileAccessLog.objects.create(
        user=user,
        file_name=file_name,
        action=action,
        ip_address=request.META.get('REMOTE_ADDR', 'Unknown')
    )

    print(f"Log saved: {log_entry}")
