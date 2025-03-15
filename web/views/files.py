"""File operation views for web interface."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator

from core.minio.node import node_manager
from core.services import FileService
from monitoring.utils import log_file_action

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

        for file_upload in files:
            try:
                file_metadata, _ = FileService.upload_file(file_upload, request.user)
                log_file_action(request.user, file_metadata.file_name, 'UPLOAD', request)
                uploaded_files.append({
                    "file_url": f'/detail/{file_metadata.id}',
                    "file_name": file_metadata.file_name
                })
            except ValueError as e:
                errors.append(str(e))

        if errors:
            return render(request, 'upload_resp.html', {"errors": errors})

        return render(request, 'upload_resp.html', {'uploaded_files': uploaded_files})

    return render(request, 'upload.html')

@login_required(login_url='/login/')
def file_detail(request, file_id):
    """Display file details and chunk information, downloading from least loaded node."""
    try:
        file_metadata = FileService.get_file_details(file_id, request.user)
        log_file_action(request.user, file_metadata.file_name, 'VIEW', request)

        # Get download URL from the least loaded node
        download_url = FileService.download_file(file_id, request.user)

        # For admin users, show distributed file status
        nodes = node_manager.get_all_nodes()
        distributed_files = [
            {
                "status": node.check_file_status(file_metadata.file_name),
                "file_url": f"http://{node.access_url}/{file_metadata.file_name}",
                "region": node.region,
            }
            for node in nodes
        ]

        chunks = file_metadata.chunks.all() if file_metadata.total_chunks > 1 else None
        return render(request, 'detail.html', {
            'file_metadata': file_metadata,
            'chunks': chunks,
            "distributed_files": distributed_files,
            'download_url': download_url,  # Pass the download URL to the template
        })
    except Exception as e:
        return render(request, 'detail.html', {'error': str(e)})

@login_required(login_url='/login/')
def delete_file(request, file_id):
    """Delete file and its chunks."""
    try:
        file_metadata = FileService.get_file_details(file_id, request.user)
        file_name = file_metadata.file_name
        FileService.delete_file(file_id, request.user)
        log_file_action(request.user, file_name, "DELETE", request)
        return JsonResponse({"message": "File deleted successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required(login_url='/login/')
def load_storage(request):
    """Display storage page with paginated file list."""
    try:
        page = int(request.GET.get('page', 1))
        uploads, total = FileService.list_files(request.user, page)
        return render(request, 'storage.html', {'uploads': uploads, "total": total})
    except Exception as e:
        return render(request, 'storage.html', {'error': str(e)})
