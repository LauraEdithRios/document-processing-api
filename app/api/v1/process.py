import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.process import (
    ProcessListItemResponse,
    ProcessResponse,
    ProcessResultResponse,
    ProgressResponse,
)
from app.services import process_service

router = APIRouter()

def build_progress_response(process) -> ProgressResponse:
    return ProgressResponse(
        total_files=process.total_files,
        processed_files=process.processed_files,
        percentage=process.percentage,
    )


def build_process_response(process, result=None) -> ProcessResponse:
    result_response = None

    if result is not None:
        result_response = ProcessResultResponse(
            total_words=result.total_words,
            total_lines=result.total_lines,
            total_characters=result.total_characters,
            most_frequent_words=json.loads(result.most_frequent_words or "[]"),
            files_processed=json.loads(result.files_processed or "[]"),
            summary=result.summary,
        )

    return ProcessResponse(
        process_id=process.id,
        status=process.status,
        progress=build_progress_response(process),
        started_at=process.started_at,
        estimated_completion=None,
        results=result_response,
    )

@router.get(
    "/list",
    response_model=List[ProcessListItemResponse],
)
def list_processes(db: Session = Depends(get_db)):
    processes = process_service.list_processes(db)

    return [
        ProcessListItemResponse(
            process_id=process.id,
            status=process.status,
            progress=build_progress_response(process),
            created_at=process.created_at,
            started_at=process.started_at,
            completed_at=process.completed_at,
        )
        for process in processes
    ]

@router.post(
    "/start",
    response_model=ProcessResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_process(db: Session = Depends(get_db)):
    process = process_service.start_process(db)

    return build_process_response(process)


@router.post(
    "/stop/{process_id}",
    response_model=ProcessResponse,
)
def stop_process(process_id: str, db: Session = Depends(get_db)):
    process = process_service.stop_process(db, process_id)

    if process is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found",
        )

    return build_process_response(process)


@router.get(
    "/status/{process_id}",
    response_model=ProcessResponse,
)
def get_process_status(process_id: str, db: Session = Depends(get_db)):
    process = process_service.get_process_status(db, process_id)

    if process is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found",
        )

    return build_process_response(process)

@router.get(
    "/results/{process_id}",
    response_model=ProcessResponse,
)
def get_process_results(process_id: str, db: Session = Depends(get_db)):
    process = process_service.get_process_status(db, process_id)

    if process is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found",
        )

    result = process_service.get_process_result(db, process_id)

    return build_process_response(process, result)