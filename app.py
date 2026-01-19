from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from config import settings
from contextlib import asynccontextmanager

from db import create_tables, alembic_manager
from views import router
import os

# Lifespan context manager must be defined before app initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown logic"""

    # --- Startup logic ---
    use_alembic = os.getenv("USE_ALEMBIC", "false").lower() == "true"
    if use_alembic:
        print("🔧 Using Alembic for database migrations...")
        alembic_manager.auto_migrate("auto migration on startup")
    else:
        print("🔧 Using SQLAlchemy create_all for database setup...")
        create_tables()

    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started successfully!")
    print(f"📍 Server running on {settings.HOST}:{settings.PORT}")
    print(f"📖 API documentation available at /docs")

    # Yield control to the app (keeps running)
    yield

    # --- Shutdown logic ---
    print(f"👋 {settings.APP_NAME} shutting down...")


# FastAPI app configuration
app = FastAPI(
    title=settings.APP_NAME,
    description="Professional business acquisition analysis and documentation platform",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security: prevent caching of admin pages to avoid back-button access after logout
async def _no_cache_middleware(request, call_next):
    response = await call_next(request)
    path = request.url.path
    # Apply no-cache headers to admin pages and other sensitive HTML endpoints
    if path.startswith("/admin"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

app.add_middleware(BaseHTTPMiddleware, dispatch=_no_cache_middleware)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routes
app.include_router(router)

# Health check endpoint
@app.get("/ping")
async def ping():
    """Simple health check endpoint"""
    return {"status": "ok", "message": "Service is running"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
