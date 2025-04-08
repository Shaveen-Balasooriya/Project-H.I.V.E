# app/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.honeypot_routes import router as honeypot_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="H.I.V.E - Honeypot Infrastructure for Vulnerability Exploration",
    description="API for managing honeypot containers",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(honeypot_router)

@app.get("/")
async def root():
    """Root endpoint returning API information"""
    return {
        "message": "Welcome to H.I.V.E API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if podman is accessible
        import podman
        client = podman.PodmanClient(base_url='unix:///tmp/podman.sock')
        version = client.version()

        return {
            "status": "healthy",
            "podman_version": version.get('Version', 'unknown'),
            "api_version": "0.1.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Could not connect to podman service. Please ensure podman is running."
        }


if __name__ == "__main__":
    # This block is used when running directly with Python
    # For production, use a proper ASGI server like uvicorn
    import uvicorn

    uvicorn.run('app.main:app', host="0.0.0.0", port=8000, reload=True)