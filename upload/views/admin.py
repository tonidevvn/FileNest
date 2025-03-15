"""Admin-specific views for web interface."""
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render

from helpers.minio.node import node_manager
from upload.models import FileMetadata

@login_required(login_url='/login/')
@staff_member_required
def admin_dashboard(request):
    """Display admin dashboard with file and node status."""
    uploads_list = FileMetadata.objects.select_related('uploaded_by').all()
    
    paginator = Paginator(uploads_list, 20)
    page_number = request.GET.get('page', 1)
    uploads = paginator.get_page(page_number)
    total = uploads_list.count()

    # Get node status
    nodes = node_manager.get_all_nodes()
    for node in nodes:
        node.is_healthy = node.check_health()

    context = {
        'uploads': uploads,
        'total': total,
        'nodes': nodes,
        'active_nodes': sum(1 for node in nodes if node.is_healthy),
        'total_nodes': len(nodes)
    }
    
    return render(request, 'dashboard.html', context)
