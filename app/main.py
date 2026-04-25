from fastapi import FastAPI
from app.api.v1.process import router as process_router

app = FastAPI(
    title="Document Processing API",
    description="Asynchronous document processing system with process tracking",
    version="1.0.0",
)

app.include_router(process_router, prefix="/process", tags=["Process"])


@app.get("/health")
def health_check():
    return {"status": "UP"}