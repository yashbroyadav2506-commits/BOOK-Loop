import os
import io
import logging
from typing import Tuple
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 Megabytes
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}


def is_allowed_file_extension(filename: str) -> bool:
    """Check file extension."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_image_magic_bytes(stream: io.BytesIO) -> Tuple[bool, str]:
    """
    Validate actual file content by checking magic bytes.
    Returns (is_valid, detected_format).
    """
    pos = stream.tell()
    header = stream.read(16)
    stream.seek(pos)  # reset stream position

    # JPEG
    if header.startswith(b'\xff\xd8\xff'):
        return True, 'jpeg'

    # PNG
    if header.startswith(b'\x89PNG\r\n\x1a\n'):
        return True, 'png'

    # WebP: 'RIFF....WEBP'
    if len(header) >= 12 and header.startswith(b'RIFF') and header[8:12] == b'WEBP':
        return True, 'webp'

    return False, 'unknown'


def upload_book_cover(file: FileStorage) -> Tuple[bool, str]:
    """
    Upload book cover image to external object storage (Cloudinary).
    Never writes to the local filesystem.
    Returns (success, secure_url_or_error_message).
    """
    if not file or not file.filename:
        return False, "No file provided."

    # Validate extension
    if not is_allowed_file_extension(file.filename):
        return False, "Unsupported file format. Please upload JPG, PNG, or WebP."

    # Read bytes into memory
    file_bytes = file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        return False, f"File size exceeds 2 MB limit (uploaded {len(file_bytes) // 1024} KB)."

    # Validate magic bytes
    stream = io.BytesIO(file_bytes)
    is_valid_image, img_format = validate_image_magic_bytes(stream)
    if not is_valid_image:
        return False, "Invalid image file. File content does not match JPG, PNG, or WebP standards."

    # Check Cloudinary configuration
    cloudinary_url = os.environ.get('CLOUDINARY_URL')
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    api_key = os.environ.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')

    if not (cloudinary_url or (cloud_name and api_key and api_secret)):
        logger.info("Cloudinary is not configured. External image storage skipped.")
        return False, "Storage provider not configured on this server. Please enter an image URL instead."

    try:
        import cloudinary
        import cloudinary.uploader

        if cloud_name and api_key and api_secret:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )

        stream.seek(0)
        upload_result = cloudinary.uploader.upload(
            stream,
            folder="pallotti_bookloop/covers",
            resource_type="image",
            transformation=[
                {'width': 800, 'height': 1200, 'crop': 'limit'},
                {'quality': 'auto:good'},
                {'fetch_format': 'auto'}
            ]
        )

        secure_url = upload_result.get('secure_url')
        if secure_url:
            return True, secure_url
        return False, "Cloudinary upload did not return a secure URL."
    except Exception as e:
        logger.error(f"Cloudinary upload exception: {str(e)}")
        return False, f"Upload to storage provider failed: {str(e)}"
