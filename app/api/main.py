from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import configs, history, sheets, sync


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_CSS_DIR = FRONTEND_DIR / "css"
FRONTEND_JS_DIR = FRONTEND_DIR / "js"
SAMPLE_DATA_DIR = PROJECT_ROOT / "sample_data"
FAVICON_PATH = FRONTEND_DIR / "favicon.svg"


# ---------------------------------------------------------
# APP
# ---------------------------------------------------------

app = FastAPI(
    title="BizSync Gateway & Web Application",
    description="Modern Business Data Synchronization Engine",
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------
# Development-safe local origins only.
# Do NOT use allow_origins=["*"] together with credentials.

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


# ---------------------------------------------------------
# STATIC FRONTEND FILES
# ---------------------------------------------------------
# Only explicitly required frontend directories are exposed.
# The project root, credentials, .env files, logs, etc. are
# intentionally NOT mounted as static directories.

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


# ---------------------------------------------------------
# FAVICON
# ---------------------------------------------------------

@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    if not FAVICON_PATH.exists():
        return {"detail": "Favicon not found"}

    return FileResponse(
        str(FAVICON_PATH),
        media_type="image/svg+xml",
    )


# ---------------------------------------------------------
# SAMPLE DATA
# ---------------------------------------------------------

@app.get("/sample_data")
def sample_data():
    return {
        "available": SAMPLE_DATA_DIR.exists(),
        "directory": str(SAMPLE_DATA_DIR),
    }


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# API ROUTERS
# ---------------------------------------------------------

app.include_router(sync.router, prefix="/api")
app.include_router(sheets.router, prefix="/api")
app.include_router(configs.router, prefix="/api")
app.include_router(history.router, prefix="/api")


# ---------------------------------------------------------
# ROOT WEB APP
# ---------------------------------------------------------

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