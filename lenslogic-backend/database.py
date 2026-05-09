import os
import json
import uuid
from typing import Generator
import logging
from sqlalchemy import (
    create_engine, Column, String, Integer,
    Text, DateTime, func
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
    photo_path = Column(Text, nullable=False)   # local file path
    encoding   = Column(Text, nullable=False)   # JSON string of 128 floats
    face_index = Column(Integer, nullable=False)
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

def save_encodings(group_id: str, photo_path: str, encodings: list[list[float]]) -> bool:
    if not encodings:
        return True

    db = SessionLocal()
    try:
        rows = [
            FaceEncoding(
                group_id=group_id,
                photo_path=photo_path,
                encoding=json.dumps(enc),   # store as JSON string
                face_index=i
            )
            for i, enc in enumerate(encodings)
        ]
        db.bulk_save_objects(rows)
        db.commit()
        logger.info(f"Saved {len(rows)} encoding(s) for {photo_path}")
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
                "photo_path": r.photo_path,
                "encoding": json.loads(r.encoding)
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Failed to fetch encodings: {e}")
        return []
    finally:
        db.close()