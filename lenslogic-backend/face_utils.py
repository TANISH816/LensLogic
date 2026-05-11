import cv2
import numpy as np
import logging
import threading

logger = logging.getLogger(__name__)

# ── Model singleton ───────────────────────────────────────────────────────────
# InsightFace is expensive to load (~1-2s). We load it ONCE at startup
# and reuse it for every request. Thread lock keeps it safe under concurrency.

_app = None
_lock = threading.Lock()


def get_model():
    """
    Lazy-load InsightFace model — only initialised on first call.
    Returns the FaceAnalysis app ready to use.
    """
    global _app
    if _app is None:
        with _lock:
            if _app is None:   # double-checked locking
                logger.info("Loading InsightFace model (first time — takes ~2s)...")
                from insightface.app import FaceAnalysis
                _app = FaceAnalysis(providers=["CPUExecutionProvider"])
                _app.prepare(ctx_id=0, det_size=(640, 640))
                logger.info("InsightFace model ready.")
    return _app


# ── Public API ────────────────────────────────────────────────────────────────

def encode_image(image_bytes: bytes) -> list[list[float]]:
    """
    Detect all faces in an image and return their 512-d embeddings.

    InsightFace returns a 512-float embedding per face (vs face_recognition's 128).
    These are normalised unit vectors, so we use cosine similarity for matching.

    Returns:
        List of 512-float lists. Empty list if no faces or on error.
    """
    try:
        # Decode bytes → OpenCV BGR image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            logger.warning("Could not decode image bytes.")
            return []

        faces = get_model().get(img)

        if not faces:
            logger.warning("No faces detected in image.")
            return []

        logger.info(f"Detected {len(faces)} face(s).")

        # face.embedding is a 512-d numpy array, already L2-normalised by InsightFace
        return [face.embedding.tolist() for face in faces]

    except Exception as e:
        logger.error(f"Error encoding image: {e}")
        return []


def find_matches(
    selfie_encoding: list[float],
    stored: list[dict],
    threshold: float = 0.4
) -> list[str]:
    """
    Vectorized cosine-similarity matching using NumPy.
    Handles 50,000 embeddings in ~0.1s.

    InsightFace embeddings are unit vectors so:
        cosine_similarity = dot(a, b)  (since ||a||=||b||=1)
    We match when similarity >= threshold (higher = more similar).

    threshold=0.4 is a good default for InsightFace 512-d embeddings.
    (equivalent to ~0.5 Euclidean distance used by face_recognition)

    Args:
        selfie_encoding : 512-float list from guest selfie
        stored          : list of dicts with keys 'encoding' and 'photo_path'
        threshold       : cosine similarity cutoff (0.0–1.0, higher = stricter)

    Returns:
        List of unique photo_path strings where the guest's face was found.
    """
    if not stored:
        return []

    # Stack all stored embeddings — shape (N, 512)
    all_encodings = np.array([s["encoding"] for s in stored], dtype=np.float32)
    selfie_array  = np.array(selfie_encoding, dtype=np.float32)

    # Normalise both (InsightFace usually returns unit vectors, but let's be safe)
    all_encodings  = all_encodings  / (np.linalg.norm(all_encodings,  axis=1, keepdims=True) + 1e-10)
    selfie_norm    = selfie_array   / (np.linalg.norm(selfie_array)  + 1e-10)

    # Cosine similarity — dot product of unit vectors — shape (N,)
    similarities = all_encodings @ selfie_norm

    match_indices = np.where(similarities >= threshold)[0]
    matched_paths = list({stored[i]["photo_path"] for i in match_indices})

    logger.info(
        f"Matched {len(matched_paths)} photo(s) from {len(stored)} encodings "
        f"(threshold={threshold}, top_sim={similarities.max():.3f})"
    )
    return matched_paths


def count_faces(image_bytes: bytes) -> int:
    """Quick helper — just returns the number of faces detected."""
    return len(encode_image(image_bytes))