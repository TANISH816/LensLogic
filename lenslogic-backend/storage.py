import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Import database functions
from database import save_photo_db, get_photo_db

# Note: UPLOAD_DIR is kept for backward compatibility but not used for storage
UPLOAD_DIR = None


def save_photo(image_bytes: bytes, group_id: str, original_filename: str) -> int | None:
    """
    Save a photo to PostgreSQL database as BLOB.
    Returns the photo_id (database primary key), or None on failure.
    """
    try:
        # Determine MIME type from filename extension
        ext = original_filename.lower().split('.')[-1]
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        photo_id = save_photo_db(group_id, original_filename, image_bytes, mime_type)
        if photo_id is None:
            logger.error(f"Failed to save photo to database: {original_filename}")
            return None
        
        logger.info(f"Saved photo: {original_filename} (ID: {photo_id}) to PostgreSQL")
        return photo_id

    except Exception as e:
        logger.error(f"Failed to save photo: {e}")
        return None


def get_photo(photo_id: int) -> bytes | None:
    """Retrieve a photo from the database."""
    try:
        result = get_photo_db(photo_id)
        if result is None:
            logger.warning(f"Photo {photo_id} not found")
            return None
        file_data, mime_type = result
        return file_data
    except Exception as e:
        logger.error(f"Failed to get photo: {e}")
        return None


def delete_group_folder(group_id: str) -> bool:
    """
    Delete all photos for a group.
    Note: Use database.delete_group_with_photos() instead for full cleanup.
    """
    logger.info(f"delete_group_folder called for {group_id} (use delete_group_with_photos from database module)")
            logger.info(f"Deleted folder for group: {group_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete group folder: {e}")
        return False