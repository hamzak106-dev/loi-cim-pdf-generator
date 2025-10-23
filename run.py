#!/usr/bin/env python3
"""
Startup script for Business Acquisition PDF Generator FastAPI application
"""

import uvicorn
from config import settings

if __name__ == "__main__":
    print("🚀 Starting Business Acquisition PDF Generator...")
    print(f"📍 Server will be available at: http://localhost:{settings.PORT}")
    print(f"📖 API docs will be available at: http://localhost:{settings.PORT}/docs")
    print(f"🔧 Environment: {'Development' if settings.DEBUG else 'Production'}")
    print("=" * 70)
    
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
