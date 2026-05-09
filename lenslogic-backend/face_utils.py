import face_recognition
import numpy as np
import logging
import io

logger = logging.getLogger(__name__)


def encode_image(image_bytes: bytes) -> list[list[float]]:
    """
    Extract all face encodings from image bytes.
    Returns list of 128-float arrays (one per face found).
    Returns [] if no faces detected or on error.
    """
    try:
        img = face_recognition.load_image_file(io.BytesIO(image_bytes))
        encodings = face_recognition.face_encodings(img)

        if not encodings:
            logger.warning("No faces detected in image.")
            return []

        logger.info(f"Detected {len(encodings)} face(s).")
        return [e.tolist() for e in encodings]

    except Exception as e:
        logger.error(f"Error encoding image: {e}")
        return []


def find_matches(
    selfie_encoding: list[float],
    stored: list[dict],
    threshold: float = 0.5
) -> list[str]:
    """
    Vectorized face matching using NumPy.
    Compares selfie against all stored encodings in one shot (~0.1s for 50k).

    Args:
        selfie_encoding : 128-float list from guest selfie
        stored          : list of dicts with keys 'encoding' and 'photo_path'
        threshold       : Euclidean distance cutoff (0.5 = good balance)

    Returns:
        List of unique photo_path strings where the guest's face was found.
    """
    if not stored:
        return []

    all_encodings = np.array([s["encoding"] for s in stored])  # shape (N, 128)
    selfie_array  = np.array(selfie_encoding)                   # shape (128,)

    # Euclidean distance from selfie to every stored face — all at once
    distances = np.linalg.norm(all_encodings - selfie_array, axis=1)

    match_indices = np.where(distances < threshold)[0]
    matched_paths = list({stored[i]["photo_path"] for i in match_indices})

    logger.info(f"Matched {len(matched_paths)} photo(s) from {len(stored)} encodings.")
    return matched_paths