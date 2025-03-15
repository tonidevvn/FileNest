"""File operation views for web interface."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from monitoring.views import log_file_action
from helpers.minio.node import node_manager
from upload.models import FileMetadata, FileChunk
from upload.utils import validate_file, handle_file_upload, delete_file

@login_required(login_url='/login/')
def file_upload(request):
    """Handle file uploads and ensure file list updates correctly."""
    if request.method == 'POST':
        files = request.FILES.getlist('file-upload')
        errors = []
        uploaded_files = []

        if not files:
            errors.append("Please select at least one file before uploading.")
            return render(request, 'upload_resp.html', {"errors": errors})

        for upload_file in files:
            file_errors = validate_file(upload_file)
            if file_errors:
                errors.extend(file_errors)

        if errors:
            return render(request, 'upload_resp.html', {"errors": errors})

        for file_upload in files:
            uploaded_file = handle_file_upload(request, file_upload)
            uploaded_files.append(uploaded_file)

        return render(request, 'upload_resp.html', {'uploaded_files': uploaded_files})

    return render(request, 'upload.html')

@login_required(login_url='/login/')
def file_detail(request, file_id):
    """Display file details and chunk information."""
    file_metadata = get_object_or_404(FileMetadata, id=file_id)
    chunks = FileChunk.objects.filter(file_metadata=file_metadata).order_by('chunk_index')
    log_file_action(request.user, file_metadata.file_name, 'VIEW', request)

    nodes = node_manager.get_all_nodes()
    distributed_files = [
        {
            "status": node.check_file_status(file_metadata.file_name),
            "file_url": f"http://{node.access_url}/{file_metadata.file_name}",
            "region": node.region,
        }
        for node in nodes
    ]

    return render(request, 'detail.html', {
        'file_metadata': file_metadata,
        'chunks': chunks,
        'distributed_files': distributed_files
    })

@login_required(login_url='/login/')
def load_storage(request):
    """Display paginated list of uploaded files."""
    uploads_list = (FileMetadata.objects.all() if request.user.is_staff 
                   else FileMetadata.objects.filter(uploaded_by=request.user))
    uploads_list = uploads_list.select_related('uploaded_by')

    paginator = Paginator(uploads_list, 20)
    page_number = request.GET.get('page', 1)
    uploads = paginator.get_page(page_number)
    total = uploads_list.count()

    return render(request, 'storage.html', {'uploads': uploads, "total": total})
