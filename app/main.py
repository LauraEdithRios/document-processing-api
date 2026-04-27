from fastapi import FastAPI

from app.api.v1.process import router as process_router
from app.core.database import Base, engine

from app.models.process import Process
from app.models.process_result import ProcessResult
from app.models.activity_log import ActivityLog

from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi import status

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Document Processing API",
    description="Asynchronous document processing system with process tracking",
    version="1.0.0",
)

@app.get("/health")
def health_check():
    return {"status": "UP"}


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)}
    )

app.include_router(process_router, prefix="/process", tags=["Process"])