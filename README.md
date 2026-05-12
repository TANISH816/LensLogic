# LensLogic

> **Intelligent Photo Sharing with Facial Recognition**  
> A modern full-stack application for collaborative photo management, powered by deep learning-based face detection and recognition.

LensLogic combines a high-performance FastAPI backend with an intuitive React frontend to create a seamless experience for group photo uploads and intelligent face-based organization. Perfect for events, family gatherings, and collaborative photography sessions.

---

## Features

✨ **Smart Face Recognition**
- Real-time facial encoding using state-of-the-art InsightFace model
- Automatic detection of matching faces across uploaded photos
- Configurable matching threshold for flexible recognition sensitivity

📸 **Multi-User Photo Upload**
- Batch upload support for efficient photo sharing
- Role-based interface (Guest & Organizer views)
- Asynchronous processing—upload photos and get results instantly

🚀 **Optimized Performance**
- Non-blocking backend with thread pool executor for CPU-heavy face processing
- Static file serving for instant photo access
- RESTful API design with CORS support for seamless frontend integration

🎨 **Modern UI**
- Built with React 19 + Vite for blazing-fast development and production builds
- Real-time status polling for upload progress
- Responsive design with Lucide icons and TailwindCSS-ready components

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | FastAPI, Uvicorn, Python 3.10+ |
| **AI/ML** | InsightFace, ONNX Runtime, OpenCV, NumPy |
| **Frontend** | React 19, Vite, Axios, React Router |
| **Database** | SQLAlchemy ORM, PostgreSQL (psycopg2) |
| **DevOps** | CORS middleware, Static file serving, Multipart uploads |

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 16+** & npm
- **Git**

### Option 1: One-Command Setup (Recommended)

**Windows:**
```cmd
run.bat
```

**macOS/Linux:**
```bash
bash run.sh
```

### Option 2: Manual Setup

#### Backend

```bash
cd lenslogic-backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd ../lenslogic-ui
npm install
npm run dev
```

Open your browser and navigate to `http://localhost:5173` (Vite will display the exact URL).

---

## Environment Configuration

Create a `.env` file in `lenslogic-backend/` to customize behavior:

```env
# PostgreSQL connection string (required for production)
DATABASE_URL=postgresql://postgres:password@localhost:5432/lenslogic

# Face matching sensitivity (0.0 - 1.0)
# Lower = stricter matching, Higher = more permissive
MATCH_THRESHOLD=0.4
```

> **Security Note:** All photos are stored as **BLOB data in PostgreSQL** (not on the filesystem). This eliminates path traversal vulnerabilities and provides:
> - Access control via database permissions
> - Encrypted storage at rest (configure in PostgreSQL)
> - Automatic backups and disaster recovery
> - Scalability for large deployments

---

## API Documentation

### Core Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/` | API status check |
| `GET` | `/health` | Health/readiness probe |
| `POST` | `/upload` | Upload and process photos |
| `GET` | `/photo/{photo_id}` | Serve a photo from database by ID |
| `GET` | `/status/{group_id}` | Get upload status for a group |
| `POST` | `/match` | Match guest selfie against group photos |

### Upload Photos

**Request:**
```http
POST /upload HTTP/1.1
Content-Type: multipart/form-data

files: [photo1.jpg, photo2.jpg, ...]
event_name: "Summer Vacation" (optional)
```

**Response:**
```json
{
  "group_id": "A1B2C3D4",
  "total_matched": 3,
  "total_searched": 15,
  "matched_photo_ids": [5, 12, 18],
  "matched_photo_urls": [
    "http://localhost:8000/photo/5",
    "http://localhost:8000/photo/12",
    "http://localhost:8000/photo/18"
  ],
  "message": "Found you in 3 photo(s)! 🎉"
}
```

---

## Project Structure

```
LensLogic/
├── lenslogic-backend/              # FastAPI application
│   ├── main.py                     # Entry point & route definitions
│   ├── face_utils.py               # Face encoding & matching logic
│   ├── storage.py                  # Database storage wrapper
│   ├── database.py                 # SQLAlchemy models & DB operations
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Environment variables (create locally)
│   └── uploads/                    # (Legacy - no longer used, kept for reference)
│
├── lenslogic-ui/                   # React + Vite frontend
│   ├── src/
│   │   ├── components/             # Reusable React components
│   │   │   ├── FileList.jsx        # Photo list display
│   │   │   ├── PhotoGrid.jsx       # Grid layout
│   │   │   ├── UploadZone.jsx      # Drag-and-drop upload
│   │   │   └── StatusPoller.jsx    # Real-time status updates
│   │   ├── pages/                  # Page components
│   │   │   ├── GuestPage.jsx       # Guest upload interface
│   │   │   └── OrganizerPage.jsx   # Organizer dashboard
│   │   ├── api/                    # API client
│   │   ├── App.jsx                 # Main app component
│   │   └── main.jsx                # React entry point
│   ├── package.json                # npm dependencies
│   ├── vite.config.js              # Vite configuration
│   └── index.html                  # HTML shell
│
├── run.bat                         # Windows startup script
├── run.sh                          # Unix startup script
└── README.md                       # This file
```

---

## Database Setup & Schema

### PostgreSQL Installation

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows:**
- Download installer from https://www.postgresql.org/download/windows/
- Or use WSL2 with: `sudo apt-get install postgresql-15`

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

### Create Database & User

```sql
-- Connect as superuser (default: postgres)
psql -U postgres

-- Create database
CREATE DATABASE lenslogic;

-- Create user
CREATE USER lenslogic_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
ALTER ROLE lenslogic_user SET client_encoding TO 'utf8';
ALTER ROLE lenslogic_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE lenslogic_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE lenslogic TO lenslogic_user;

-- Exit
\q
```

### Update .env

```env
DATABASE_URL=postgresql://lenslogic_user:your_secure_password@localhost:5432/lenslogic
```

### Database Schema (Auto-Created)

The following tables are automatically created on first startup:

**Groups Table**
```sql
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    group_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Photos Table** (BLOB Storage)
```sql
CREATE TABLE photos (
    id SERIAL PRIMARY KEY,
    group_id VARCHAR(20) NOT NULL REFERENCES groups(group_id),
    filename VARCHAR(255),
    file_data BYTEA NOT NULL,  -- Binary photo data
    file_size INTEGER,
    mime_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_photos_group_id ON photos(group_id);
```

**Face Encodings Table**
```sql
CREATE TABLE face_encodings (
    id SERIAL PRIMARY KEY,
    group_id VARCHAR(20) NOT NULL,
    photo_id INTEGER NOT NULL REFERENCES photos(id),
    encoding TEXT NOT NULL,  -- JSON array of 512 floats
    face_index INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_encodings_group_id ON face_encodings(group_id);
```

---

### Running Tests & Linting

```bash
# Frontend linting
cd lenslogic-ui
npm run lint

# Backend (add tests as needed)
cd ../lenslogic-backend
pytest  # when test suite is added
```

### Hot Reload

Both backend and frontend support hot reload during development:
- **Backend**: Uvicorn with `--reload` flag watches Python files
- **Frontend**: Vite automatically refreshes browser on component changes

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port 8000 already in use** | Change port: `uvicorn main:app --port 8001` |
| **`ModuleNotFoundError: No module named 'fastapi'`** | Activate venv and run `pip install -r requirements.txt` |
| **Frontend won't connect to backend** | Ensure backend is running on `http://localhost:8000` and CORS is enabled |
| **Face recognition too slow** | Reduce photo resolution or increase `MATCH_THRESHOLD` for faster processing |
| **`npm: command not found`** | Install Node.js from https://nodejs.org/ |

---

## Performance Notes

- **Face encoding**: Runs in background thread pool (non-blocking)
- **Upload handling**: Supports batch uploads with multipart/form-data
- **Photo storage**: Stored as BYTEA (binary large objects) in PostgreSQL
- **Database**: SQLAlchemy ORM with optimized queries and indexing on group_id and photo_id

---

## Future Enhancements

- [ ] Real-time WebSocket updates for upload progress
- [ ] Advanced filtering by date, location, or face clusters
- [ ] Image optimization and resizing pipeline
- [ ] User authentication & role-based access control
- [ ] Cloud storage integration (S3, GCS)
- [ ] Mobile-responsive UI improvements

---

## License

This repository does not currently include a license. Add one to clarify reuse permissions and community contribution guidelines.
