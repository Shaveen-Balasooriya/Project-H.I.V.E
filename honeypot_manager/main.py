# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

from controllers.honeypot_manager_controller import router as honeypot_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("honeypot_manager.log")
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Honeypot Manager API",
    description="API for managing honeypot containers",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(honeypot_router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Honeypot Manager API. Navigate to /docs for API documentation."}

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        # Simple health check - could include additional checks here
        return {"status": "ok", "version": "1.0.0"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)