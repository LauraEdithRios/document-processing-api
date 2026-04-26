from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.process import Process
from app.models.process_status import ProcessStatus
from app.repositories import process_repository


def start_process(db: Session) -> Process:
    process_id = str(uuid4())

    process = Process(
        id=process_id,
        status=ProcessStatus.PENDING.value,
        total_files=0,
        processed_files=0,
        percentage=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    created_process = process_repository.create_process(db, process)

    process_repository.add_activity_log(
        db=db,
        process_id=created_process.id,
        message="Process created with PENDING status",
    )

    return created_process


def get_process_status(
    db: Session,
    process_id: str,
) -> Optional[Process]:
    return process_repository.get_process_by_id(db, process_id)


def list_processes(db: Session) -> List[Process]:
    return process_repository.list_processes(db)


def stop_process(
    db: Session,
    process_id: str,
) -> Optional[Process]:
    process = process_repository.get_process_by_id(db, process_id)

    if process is None:
        return None

    if process.status in [
        ProcessStatus.COMPLETED.value,
        ProcessStatus.FAILED.value,
        ProcessStatus.STOPPED.value,
    ]:
        return process

    updated_process = process_repository.update_process_status(
        db=db,
        process_id=process_id,
        status=ProcessStatus.STOPPED.value,
    )

    process_repository.add_activity_log(
        db=db,
        process_id=process_id,
        message="Process manually stopped",
    )

    return updated_process


def get_process_result(
    db: Session,
    process_id: str,
):
    process = process_repository.get_process_by_id(db, process_id)

    if process is None:
        return None

    return process_repository.get_process_result(db, process_id)