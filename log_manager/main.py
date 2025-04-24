from fastapi import FastAPI
from controllers.log_manager import router as log_manager_router

app = FastAPI(
    title="Project H.I.V.E Log Manager API",
    description="Manage NATS server and log collector containers",
    version="1.0.0",
)

app.include_router(log_manager_router, prefix="/log_manager", tags=["log_manager"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8081,
        reload=True,
        log_level="info",
    )
