import logging
import time

from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.process import router as process_router
from app.core.database import Base, engine
from app.core.logging_config import setup_logging
from app.models.activity_log import ActivityLog
from app.models.process import Process
from app.models.process_result import ProcessResult

setup_logging()

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document Processing API",
    description="Asynchronous document processing system with process tracking",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(process_router, prefix="/process", tags=["Process"])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000)
    logger.info(
        "http request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.get("/health")
def health_check():
    return {"status": "UP"}


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )

@app.get("/", include_in_schema=False)
def ui():
    return FileResponse("static/index.html")
