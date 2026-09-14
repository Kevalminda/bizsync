from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import configs, history, sheets, sync


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_CSS_DIR = FRONTEND_DIR / "css"
FRONTEND_JS_DIR = FRONTEND_DIR / "js"
SAMPLE_DATA_DIR = PROJECT_ROOT / "sample_data"
FAVICON_PATH = FRONTEND_DIR / "favicon.svg"


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="BizSync Gateway & Web Application",
    description="Modern Business Data Synchronization Engine",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================
# Local development origins only.
# Do not use allow_origins=["*"] with credentials.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
)


# =========================================================
# FRONTEND STATIC FILES
# =========================================================
# Only explicitly required frontend directories are exposed.
# The project root is NOT mounted.

if FRONTEND_CSS_DIR.exists():
    app.mount(
        "/css",
        StaticFiles(directory=str(FRONTEND_CSS_DIR)),
        name="css",
    )

if FRONTEND_JS_DIR.exists():
    app.mount(
        "/js",
        StaticFiles(directory=str(FRONTEND_JS_DIR)),
        name="js",
    )


# =========================================================
# FAVICON
# =========================================================

@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    if not FAVICON_PATH.exists():
        return {"detail": "Favicon not found"}

    return FileResponse(
        str(FAVICON_PATH),
        media_type="image/svg+xml",
    )


# =========================================================
# SAMPLE DATA INFO
# =========================================================

@app.get("/sample_data")
def sample_data():
    return {
        "available": SAMPLE_DATA_DIR.exists(),
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/api/health")
def health_check():
    credentials_path = PROJECT_ROOT / "credentials.json"
    authorized_user_path = PROJECT_ROOT / "authorized_user.json"

    return {
        "status": "healthy",
        "service": "BizSync",
        "version": "1.0.0",
        "google_credentials_present": credentials_path.exists(),
        "google_authorized_user_present": authorized_user_path.exists(),
    }


# =========================================================
# API ROUTERS
# =========================================================
# These were missing from the app instance seen by the tests.

app.include_router(sync.router)
app.include_router(sheets.router)
app.include_router(configs.router)
app.include_router(history.router)

# =========================================================
# FRONTEND ENTRY POINT
# =========================================================

@app.get("/", include_in_schema=False)
def serve_frontend():
    index_path = FRONTEND_DIR / "index.html"

    if not index_path.exists():
        return {
            "service": "BizSync",
            "status": "running",
            "message": "Frontend index.html not found.",
        }

    return FileResponse(
        str(index_path),
        media_type="text/html",
    )
