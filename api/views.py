from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from storage.models import FileMetadata, FileChunk
from storage.utils import chunk_file, upload_chunk_to_s3

class FileUploadView(APIView):
    """Uploads file, splits it into chunks, and stores in AWS S3."""

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        file_metadata = FileMetadata.objects.create(
            file_name=file.name,
            file_hash=hash(file),  # Hash entire file for deduplication
            total_chunks=0
        )

        chunks = chunk_file(file)

        for index, chunk_data, chunk_hash in chunks:
            s3_key = f"chunks/{file_metadata.file_hash}/{index}.chunk"
            upload_chunk_to_s3(chunk_data, s3_key)

            FileChunk.objects.create(
                file=file_metadata,
                chunk_index=index,
                chunk_hash=chunk_hash,
                s3_key=s3_key
            )

        file_metadata.total_chunks = len(chunks)
        file_metadata.save()

        return Response({"message": "File uploaded in chunks", "file_hash": file_metadata.file_hash}, status=201)

class FileDownloadView(APIView):
    """Reconstructs and serves the file from S3 chunks."""

    def get(self, request, file_hash):
        file_meta = get_object_or_404(FileMetadata, file_hash=file_hash)
        file_chunks = FileChunk.objects.filter(file=file_meta).order_by("chunk_index")

        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        reconstructed_file = b""
        for chunk in file_chunks:
            chunk_obj = s3_client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=chunk.s3_key)
            reconstructed_file += chunk_obj['Body'].read()

        response = Response(reconstructed_file, content_type="application/octet-stream")
        response['Content-Disposition'] = f'attachment; filename="{file_meta.file_name}"'
        return response
