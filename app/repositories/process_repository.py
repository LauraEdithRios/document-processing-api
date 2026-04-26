from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.process import Process
from app.models.process_result import ProcessResult


def create_process(db: Session, process: Process) -> Process:
    db.add(process)
    db.commit()
    db.refresh(process)
    return process


def get_process_by_id(db: Session, process_id: str) -> Optional[Process]:
    return db.query(Process).filter(Process.id == process_id).first()


def list_processes(db: Session) -> List[Process]:
    return db.query(Process).order_by(Process.created_at.desc()).all()


def update_process_status(
    db: Session,
    process_id: str,
    status: str,
    error_message: Optional[str] = None,
) -> Optional[Process]:
    process = get_process_by_id(db, process_id)

    if process is None:
        return None

    process.status = status
    process.updated_at = datetime.utcnow()

    if error_message:
        process.error_message = error_message

    if status in ["COMPLETED", "FAILED", "STOPPED"]:
        process.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(process)

    return process


def update_process_progress(
    db: Session,
    process_id: str,
    processed_files: int,
    total_files: int,
) -> Optional[Process]:
    process = get_process_by_id(db, process_id)

    if process is None:
        return None

    percentage = 0
    if total_files > 0:
        percentage = int((processed_files / total_files) * 100)

    process.processed_files = processed_files
    process.total_files = total_files
    process.percentage = percentage
    process.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(process)

    return process


def save_process_result(
    db: Session,
    result: ProcessResult,
) -> ProcessResult:
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_process_result(
    db: Session,
    process_id: str,
) -> Optional[ProcessResult]:
    return (
        db.query(ProcessResult)
        .filter(ProcessResult.process_id == process_id)
        .first()
    )


def add_activity_log(
    db: Session,
    process_id: str,
    message: str,
) -> ActivityLog:
    log = ActivityLog(
        process_id=process_id,
        message=message,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log


def list_activity_logs(
    db: Session,
    process_id: str,
) -> List[ActivityLog]:
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.process_id == process_id)
        .order_by(ActivityLog.created_at.asc())
        .all()
    )