import os
import uuid
import logging
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))


def get_group_folder(group_id: str) -> Path:
    """Returns (and creates) the folder for a group's photos."""
    folder = UPLOAD_DIR / group_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_photo(image_bytes: bytes, group_id: str, original_filename: str) -> str | None:
    """
    Save a photo to the local uploads/group_id/ folder.
    Returns the relative file path (used as the photo identifier).
    """
    try:
        ext = Path(original_filename).suffix.lower() or ".jpg"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        folder = get_group_folder(group_id)
        file_path = folder / unique_name

        with open(file_path, "wb") as f:
            f.write(image_bytes)

        # Return a forward-slash path for consistency across OS
        relative_path = f"{group_id}/{unique_name}"
        logger.info(f"Saved photo: uploads/{relative_path}")
        return relative_path

    except Exception as e:
        logger.error(f"Failed to save photo: {e}")
        return None


def delete_group_folder(group_id: str) -> bool:
    """Delete all photos for a group."""
    try:
        folder = UPLOAD_DIR / group_id
        if folder.exists():
            shutil.rmtree(folder)
            logger.info(f"Deleted folder for group: {group_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete group folder: {e}")
        return False