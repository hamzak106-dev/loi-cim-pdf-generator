from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from db import create_tables, alembic_manager
from views import router
import os

# FastAPI app configuration
app = FastAPI(
    title=settings.APP_NAME,
    description="Professional business acquisition analysis and documentation platform",
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routes
app.include_router(router)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup"""
    
    # Check if Alembic auto-migration is enabled
    use_alembic = os.getenv("USE_ALEMBIC", "false").lower() == "true"
    
    if use_alembic:
        print("🔧 Using Alembic for database migrations...")
        # Auto-initialize and migrate with Alembic
        alembic_manager.auto_migrate("auto migration on startup")
    else:
        print("🔧 Using SQLAlchemy create_all for database setup...")
        # Traditional SQLAlchemy create_all
        create_tables()
    
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started successfully!")
    print(f"📍 Server running on {settings.HOST}:{settings.PORT}")
    print(f"📖 API documentation available at /docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    print(f"👋 {settings.APP_NAME} shutting down...")

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
