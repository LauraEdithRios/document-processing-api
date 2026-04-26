from fastapi import FastAPI

from app.api.v1.process import router as process_router
from app.core.database import Base, engine

from app.models.process import Process
from app.models.process_result import ProcessResult
from app.models.activity_log import ActivityLog

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document Processing API",
    description="Asynchronous document processing system with process tracking",
    version="1.0.0",
)

app.include_router(process_router, prefix="/process", tags=["Process"])


@app.get("/health")
def health_check():
    return {"status": "UP"}