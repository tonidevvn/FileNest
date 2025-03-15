"""API Views for FileNest."""
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.services import FileService
from core.auth import AuthService
from .serializers import FileMetadataSerializer, UserSerializer
from .auth import CustomTokenAuthentication  # Import custom token auth

# Common authentication and permission classes
AUTH_CLASSES = [CustomTokenAuthentication]
PERM_CLASSES = [IsAuthenticated]

def create_response(success=True, message="", data=None, status_code=status.HTTP_200_OK):
    """Create a standardized response format."""
    return Response(
        {
            "success": success,
            "message": message,
            "data": data or {},
        },
        status=status_code,
    )

@api_view(["POST"])
def signup(request):
    """Register a new user and return their token."""
    try:
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user, token = AuthService.create_user(
                username=request.data["username"],
                email=request.data["email"],
                password=request.data["password"]
            )
            return create_response(
                message="User registered successfully",
                data={"token": token.key, "user": serializer.data},
                status_code=status.HTTP_201_CREATED,
            )
        return create_response(
            success=False,
            message="Invalid registration data",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except ValueError as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

@api_view(["POST"])
def login(request):
    """Log in a user and return their token."""
    try:
        user = AuthService.validate_login(
            username=request.data["username"],
            password=request.data["password"]
        )
        token = AuthService.get_or_create_token(user)
        serializer = UserSerializer(user)
        return create_response(
            message="Login successful",
            data={"token": token.key, "user": serializer.data},
        )
    except ValueError as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

@api_view(["POST"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def upload_file(request):
    """Upload a file for authenticated users."""
    try:
        if "file-upload" not in request.FILES:
            return create_response(
                success=False,
                message="No file provided",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        file_metadata, _ = FileService.upload_file(request.FILES["file-upload"], request.user)
        return create_response(
            message="File uploaded successfully",
            data=FileMetadataSerializer(file_metadata).data,
            status_code=status.HTTP_201_CREATED,
        )
    except ValueError as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

@api_view(["GET"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def detail_file(request, file_id):
    """Get file details for authorized users."""
    try:
        file_obj = FileService.get_file_details(file_id, request.user)
        serializer = FileMetadataSerializer(file_obj)
        return create_response(
            message="File details retrieved",
            data=serializer.data,
        )
    except Exception as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["DELETE"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def delete_file(request, file_id):
    """Delete a file for authorized users."""
    try:
        FileService.delete_file(file_id, request.user)
        return create_response(message="File deleted successfully")
    except Exception as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["GET"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def list_files(request):
    """List all uploaded files for the authenticated user."""
    try:
        page = int(request.GET.get('page', 1))
        files, total = FileService.list_files(request.user, page)
        serializer = FileMetadataSerializer(files, many=True)
        return create_response(
            message="Files retrieved successfully",
            data={"files": serializer.data, "count": total},
        )
    except Exception as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["GET"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def download_file(request, file_id):
    """Download a file for authenticated users."""
    try:
        use_cache = request.GET.get("no_cache", "0") != "1"
        return FileService.download_file(file_id, request.user, use_cache)
    except Exception as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
