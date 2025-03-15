"""Admin views for web interface."""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from core.minio.node import node_manager
from core.services import FileService


def is_staff(user):
    """Check if user is staff member."""
    return user.is_staff


@login_required(login_url="/login/")
@user_passes_test(is_staff)
def admin_dashboard(request):
    """Display admin dashboard with file and node status."""
    try:
        page = int(request.GET.get("page", 1))
        uploads, total = FileService.list_files(request.user, page)

        # Get node status
        nodes = node_manager.get_all_nodes()

        return render(
            request,
            "dashboard.html",
            {"uploads": uploads, "total": total, "nodes": nodes},
        )
    except Exception as e:
        return render(request, "dashboard.html", {"error": str(e)})
