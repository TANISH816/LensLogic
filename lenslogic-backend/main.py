import os
import uuid
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from face_utils import encode_image, find_matches
from storage import save_photo, UPLOAD_DIR
from database import (
    init_db,
    create_group,
    group_exists,
    get_group_status,
    save_encodings,
    get_encodings_for_group
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", 0.5))

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="LensLogic API",
    description="Local facial recognition photo sharing.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # React dev server on localhost
    allow_methods=["*"],
    allow_headers=["*"]
)

# Serve uploaded photos as static files
# e.g. http://localhost:8000/uploads/ABC12345/photo.jpg
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("LensLogic API started. DB tables ready.")


# ── Helpers ───────────────────────────────────────────────────────────────────

def generate_group_id() -> str:
    """Short 8-char uppercase ID e.g. 'A3F9B2C1'. Guaranteed unique."""
    while True:
        gid = uuid.uuid4().hex[:8].upper()
        if not group_exists(gid):
            return gid


# ── Background task ───────────────────────────────────────────────────────────

async def process_photos_background(files_data: list[tuple[str, bytes]], group_id: str):
    """
    Runs after the organizer gets their Group ID.
    For each photo:
      1. Save to local disk (uploads/group_id/)
      2. Encode all faces in it
      3. Save encodings to PostgreSQL
    """
    logger.info(f"[BG] Processing {len(files_data)} photo(s) for group {group_id}")

    for filename, image_bytes in files_data:
        try:
            # 1. Save photo to disk
            photo_path = save_photo(image_bytes, group_id, filename)
            if not photo_path:
                logger.warning(f"[BG] Could not save {filename}, skipping.")
                continue

            # 2. Extract face encodings
            encodings = encode_image(image_bytes)

            # 3. Save to DB (even if 0 faces — just no rows inserted)
            save_encodings(group_id, photo_path, encodings)

            logger.info(f"[BG] {filename} → {len(encodings)} face(s) encoded.")
            await asyncio.sleep(0)  # yield to event loop between photos

        except Exception as e:
            logger.error(f"[BG] Error on {filename}: {e}")
            continue

    logger.info(f"[BG] Done processing group {group_id}.")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "LensLogic API is running 🚀"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_photos(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    event_name: str = Query(default="", description="Optional event/album name")
):
    """
    Organizer uploads photos.
    → Instantly returns Group ID.
    → Photo saving + face encoding runs in the background.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    # Read all bytes before returning (can't read after response is sent)
    files_data = []
    for f in files:
        content = await f.read()
        if content:
            files_data.append((f.filename, content))

    if not files_data:
        raise HTTPException(status_code=400, detail="All uploaded files were empty.")

    # Create group in DB
    group_id = generate_group_id()
    create_group(group_id, name=event_name)

    # Start background encoding
    background_tasks.add_task(process_photos_background, files_data, group_id)

    return {
        "group_id": group_id,
        "total_photos": len(files_data),
        "status": "processing",
        "message": f"Share this Group ID with guests: {group_id}. Encoding is running in the background."
    }


@app.get("/status/{group_id}")
def check_status(group_id: str):
    """
    Poll this to see how many face encodings are done.
    Organizer can show a progress indicator on the frontend.
    """
    status = get_group_status(group_id)
    if not status:
        raise HTTPException(status_code=404, detail="Group not found.")
    return status


@app.post("/match")
async def match_face(
    group_id: str = Query(..., description="Group ID from the organizer"),
    selfie: UploadFile = File(..., description="Guest selfie photo")
):
    """
    Guest uploads their selfie + Group ID.
    Returns all photo URLs from the group where their face was found.

    Speed: < 1 second even for 50,000 stored encodings.
    """
    # Check group exists
    if not group_exists(group_id):
        raise HTTPException(status_code=404, detail="Group ID not found. Please check and try again.")

    # Read selfie
    selfie_bytes = await selfie.read()
    if not selfie_bytes:
        raise HTTPException(status_code=400, detail="Selfie is empty.")

    # Encode selfie
    selfie_encodings = encode_image(selfie_bytes)
    if not selfie_encodings:
        raise HTTPException(
            status_code=422,
            detail="No face detected in your selfie. Please use a clear, well-lit photo."
        )

    if len(selfie_encodings) > 1:
        logger.warning(f"Multiple faces in selfie — using the largest/first face.")

    selfie_encoding = selfie_encodings[0]

    # Load all stored encodings for this group
    stored = get_encodings_for_group(group_id)
    if not stored:
        raise HTTPException(
            status_code=404,
            detail="No photos processed yet for this group. Please wait a moment and try again."
        )

    # NumPy vectorized match
    matched_paths = find_matches(selfie_encoding, stored, threshold=MATCH_THRESHOLD)

    # Build full URLs so frontend can display images directly
    base_url = "http://localhost:8000/uploads"
    matched_urls = [f"{base_url}/{path}" for path in matched_paths]

    return {
        "group_id": group_id,
        "total_matched": len(matched_urls),
        "total_searched": len(stored),
        "matched_photos": matched_urls,
        "message": (
            f"Found you in {len(matched_urls)} photo(s)! 🎉"
            if matched_urls else
            "No matches found. Try a clearer selfie or check the Group ID."
        )
    }