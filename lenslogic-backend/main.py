import os
import uuid
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from face_utils import encode_image, find_matches, get_model
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

MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", 0.4))

# Thread pool — face_recognition is CPU-bound and blocks asyncio if run directly
executor = ThreadPoolExecutor(max_workers=2)

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="LensLogic API",
    description="Local facial recognition photo sharing.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    init_db()
    executor.submit(get_model)  # warm up InsightFace model immediately
    logger.info("LensLogic API started. DB tables ready.")


# ── Helpers ───────────────────────────────────────────────────────────────────

def generate_group_id() -> str:
    while True:
        gid = uuid.uuid4().hex[:8].upper()
        if not group_exists(gid):
            return gid


# ── Background task — runs in thread pool so it never blocks the event loop ───

def process_one_photo(filename: str, image_bytes: bytes, group_id: str):
    """Synchronous worker: save photo + encode faces + store to DB."""
    try:
        photo_path = save_photo(image_bytes, group_id, filename)
        if not photo_path:
            logger.warning(f"[BG] Could not save {filename}, skipping.")
            return

        encodings = encode_image(image_bytes)
        save_encodings(group_id, photo_path, encodings)
        logger.info(f"[BG] {filename} → {len(encodings)} face(s) encoded.")

    except Exception as e:
        logger.error(f"[BG] Error on {filename}: {e}")


def process_photos_sync(files_data: list, group_id: str):
    """Called in a thread — processes all photos sequentially."""
    logger.info(f"[BG] Starting {len(files_data)} photo(s) for group {group_id}")
    for filename, image_bytes in files_data:
        process_one_photo(filename, image_bytes, group_id)
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
    files: list[UploadFile] = File(...),
    event_name: str = Query(default="", description="Optional event/album name")
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    files_data = []
    for f in files:
        content = await f.read()
        if content:
            files_data.append((f.filename, content))

    if not files_data:
        raise HTTPException(status_code=400, detail="All uploaded files were empty.")

    group_id = generate_group_id()
    create_group(group_id, name=event_name)

    # Submit to thread pool — does NOT block the event loop
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, process_photos_sync, files_data, group_id)

    return {
        "group_id": group_id,
        "total_photos": len(files_data),
        "status": "processing",
        "message": f"Share this Group ID with guests: {group_id}. Encoding is running in the background."
    }


@app.get("/status/{group_id}")
def check_status(group_id: str):
    status = get_group_status(group_id)
    if not status:
        raise HTTPException(status_code=404, detail="Group not found.")
    return status


@app.post("/match")
async def match_face(
    group_id: str = Query(..., description="Group ID from the organizer"),
    selfie: UploadFile = File(..., description="Guest selfie photo")
):
    if not group_exists(group_id):
        raise HTTPException(status_code=404, detail="Group ID not found. Please check and try again.")

    selfie_bytes = await selfie.read()
    if not selfie_bytes:
        raise HTTPException(status_code=400, detail="Selfie is empty.")

    # Run encoding in thread pool so it doesn't block
    loop = asyncio.get_event_loop()
    selfie_encodings = await loop.run_in_executor(executor, encode_image, selfie_bytes)

    if not selfie_encodings:
        raise HTTPException(
            status_code=422,
            detail="No face detected in your selfie. Please use a clear, well-lit photo."
        )

    selfie_encoding = selfie_encodings[0]

    stored = get_encodings_for_group(group_id)
    if not stored:
        raise HTTPException(
            status_code=404,
            detail="No photos processed yet for this group. Please wait a moment and try again."
        )

    matched_paths = find_matches(selfie_encoding, stored, threshold=MATCH_THRESHOLD)

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