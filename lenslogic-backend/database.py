import os
import json
import uuid
from typing import Generator
import logging
from sqlalchemy import (
    create_engine, Column, String, Integer,
    Text, DateTime, func, LargeBinary
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lenslogic")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ── Models ────────────────────────────────────────────────────────────────────

class Group(Base):
    __tablename__ = "groups"

    id         = Column(Integer, primary_key=True, index=True)
    group_id   = Column(String(20), unique=True, nullable=False, index=True)
    name       = Column(String(200), default="")
    created_at = Column(DateTime, server_default=func.now())


class FaceEncoding(Base):
    __tablename__ = "face_encodings"

    id         = Column(Integer, primary_key=True, index=True)
    group_id   = Column(String(20), nullable=False, index=True)
    photo_id   = Column(Integer, nullable=False, index=True)  # FK to Photo.id
    encoding   = Column(Text, nullable=False)   # JSON string of 128 floats
    face_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Photo(Base):
    __tablename__ = "photos"

    id         = Column(Integer, primary_key=True, index=True)
    group_id   = Column(String(20), nullable=False, index=True)
    filename   = Column(String(255), nullable=False)
    file_data  = Column(LargeBinary, nullable=False)  # BLOB storage
    file_size  = Column(Integer, nullable=False)  # in bytes
    mime_type  = Column(String(50), default="image/jpeg")
    created_at = Column(DateTime, server_default=func.now())


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Group operations ──────────────────────────────────────────────────────────

def create_group(group_id: str, name: str = "") -> bool:
    db = SessionLocal()
    try:
        db.add(Group(group_id=group_id, name=name))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create group: {e}")
        return False
    finally:
        db.close()


def group_exists(group_id: str) -> bool:
    db = SessionLocal()
    try:
        return db.query(Group).filter(Group.group_id == group_id).first() is not None
    finally:
        db.close()


def get_group_status(group_id: str) -> dict | None:
    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            return None
        count = db.query(FaceEncoding).filter(FaceEncoding.group_id == group_id).count()
        return {
            "group_id": group.group_id,
            "name": group.name,
            "created_at": str(group.created_at),
            "total_encodings": count
        }
    finally:
        db.close()


# ── Encoding operations ───────────────────────────────────────────────────────

def save_encodings(group_id: str, photo_id: int, encodings: list[list[float]]) -> bool:
    if not encodings:
        return True

    db = SessionLocal()
    try:
        rows = [
            FaceEncoding(
                group_id=group_id,
                photo_id=photo_id,
                encoding=json.dumps(enc),   # store as JSON string
                face_index=i
            )
            for i, enc in enumerate(encodings)
        ]
        db.bulk_save_objects(rows)
        db.commit()
        logger.info(f"Saved {len(rows)} encoding(s) for photo_id {photo_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save encodings: {e}")
        return False
    finally:
        db.close()


def get_encodings_for_group(group_id: str) -> list[dict]:
    db = SessionLocal()
    try:
        rows = db.query(FaceEncoding).filter(FaceEncoding.group_id == group_id).all()
        return [
            {
                "photo_id": r.photo_id,
                "encoding": json.loads(r.encoding)
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Failed to fetch encodings: {e}")
        return []
    finally:
        db.close()


# ── Photo operations (BLOB storage in PostgreSQL) ─────────────────────────────

def save_photo_db(group_id: str, filename: str, file_data: bytes, mime_type: str = "image/jpeg") -> int | None:
    """
    Save photo as BLOB in PostgreSQL.
    Returns photo_id for use in encodings, or None on failure.
    """
    db = SessionLocal()
    try:
        photo = Photo(
            group_id=group_id,
            filename=filename,
            file_data=file_data,
            file_size=len(file_data),
            mime_type=mime_type
        )
        db.add(photo)
        db.commit()
        db.refresh(photo)
        logger.info(f"Saved photo {filename} (ID: {photo.id}) to database")
        return photo.id
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save photo to DB: {e}")
        return None
    finally:
        db.close()


def get_photo_db(photo_id: int) -> tuple[bytes, str] | None:
    """
    Retrieve photo BLOB from PostgreSQL.
    Returns (file_data, mime_type) or None if not found.
    """
    db = SessionLocal()
    try:
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            return None
        return (photo.file_data, photo.mime_type)
    except Exception as e:
        logger.error(f"Failed to fetch photo {photo_id}: {e}")
        return None
    finally:
        db.close()


def get_photos_for_group(group_id: str) -> list[dict]:
    """Get all photos for a group with their metadata."""
    db = SessionLocal()
    try:
        photos = db.query(Photo).filter(Photo.group_id == group_id).all()
        return [
            {
                "id": p.id,
                "filename": p.filename,
                "file_size": p.file_size,
                "mime_type": p.mime_type,
                "created_at": str(p.created_at)
            }
            for p in photos
        ]
    except Exception as e:
        logger.error(f"Failed to fetch photos for group {group_id}: {e}")
        return []
    finally:
        db.close()


def delete_group_with_photos(group_id: str) -> bool:
    """Delete group and all associated photos/encodings."""
    db = SessionLocal()
    try:
        db.query(FaceEncoding).filter(FaceEncoding.group_id == group_id).delete()
        db.query(Photo).filter(Photo.group_id == group_id).delete()
        db.query(Group).filter(Group.group_id == group_id).delete()
        db.commit()
        logger.info(f"Deleted group {group_id} and all associated data")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete group {group_id}: {e}")
        return False
    finally:
        db.close()