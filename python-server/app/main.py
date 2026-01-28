"""
Celebium FastAPI Application
Browser Profile Manager with SeleniumBase Integration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from app.core.config import settings
from app.core.database import init_db

# Create FastAPI app
app = FastAPI(
    title="Celebium API",
    description="Browser Profile Manager with SeleniumBase Integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (allow Electron app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        f"http://localhost:{settings.API_PORT}",
        f"http://127.0.0.1:{settings.API_PORT}"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print("=" * 50)
    print("🚀 Starting Celebium API Server")
    print("=" * 50)

    # Initialize database
    init_db()
    print("✅ Database initialized")

    # Ensure profiles directory exists
    if not os.path.exists(settings.PROFILES_DIR):
        os.makedirs(settings.PROFILES_DIR)
    print(f"✅ Profiles directory: {settings.PROFILES_DIR}")

    print(f"✅ Server running on http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\n" + "=" * 50)
    print("🛑 Shutting down Celebium API Server")

    # Close all running profiles
    from app.api.profiles import selenium_manager
    selenium_manager.close_all()

    print("✅ Cleanup complete")
    print("=" * 50)


# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint - API information"""
    return {
        "name": "Celebium API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "description": "Browser Profile Manager with SeleniumBase Integration"
    }


# System endpoints
@app.get("/status")
def get_status():
    """Check if server is running"""
    return {
        "code": 0,
        "status": "success",
        "data": {}
    }


# Include API routers
from app.api import profiles, system, proxies, auth
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(system.router, tags=["System"])
app.include_router(profiles.router, prefix="/profile", tags=["Profiles"])
app.include_router(proxies.router, prefix="/proxies", tags=["Proxies"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,  # Auto-reload in development
        log_level="info"
    )
