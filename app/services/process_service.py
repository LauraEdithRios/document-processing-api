import json
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.process import Process
from app.models.process_result import ProcessResult
from app.models.process_status import ProcessStatus
from app.repositories import process_repository
from app.workers.document_worker import process_documents


def start_process(db: Session) -> Process:
    """
    Crea un nuevo proceso y lo deja en estado PENDING.
    El procesamiento real se ejecuta después en background.
    """
    process_id = str(uuid4())

    # Valida que no exista un proceso con el mismo ID 
    if process_repository.get_process_by_id(db, process_id):
        process_repository.add_activity_log(db, process_id, "Intento de crear proceso duplicado", level="ERROR")
        raise ValueError("Ya existe un proceso con ese ID")

    process = Process(
        id=process_id,
        status=ProcessStatus.PENDING.value,
        total_files=0,
        processed_files=0,
        percentage=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    try:
        created_process = process_repository.create_process(db, process)
        process_repository.add_activity_log(
            db=db,
            process_id=created_process.id,
            message="Process created with PENDING status",
            level="INFO"
        )
        return created_process
    except Exception as e:
        process_repository.add_activity_log(db, process_id, f"Error al crear proceso: {str(e)}", level="ERROR")
        raise


def get_process_status(
    db: Session,
    process_id: str,
) -> Optional[Process]:
    if not process_id:
        raise ValueError("process_id no puede ser None")
    # Valida formato UUID
    try:
        import uuid
        uuid.UUID(process_id)
    except Exception:
        process_repository.add_activity_log(db, process_id, "process_id con formato inválido", level="ERROR")
        raise ValueError("process_id con formato inválido")
    return process_repository.get_process_by_id(db, process_id)


def list_processes(db: Session) -> List[Process]:
    return process_repository.list_processes(db)


def stop_process(
    db: Session,
    process_id: str,
) -> Optional[Process]:
    if not process_id:
        raise ValueError("process_id no puede ser None")
    process = process_repository.get_process_by_id(db, process_id)
    if process is None:
        process_repository.add_activity_log(db, process_id, "Intento de detener proceso inexistente", level="ERROR")
        return None

    # Solo se puede detener si está en RUNNING o PENDING
    if process.status not in [ProcessStatus.RUNNING.value, ProcessStatus.PENDING.value]:
        process_repository.add_activity_log(db, process_id, f"Intento de detener proceso en estado {process.status}", level="WARNING")
        return None

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


def _execute_process(process_id: str, db: Session) -> None:
    """
    Lógica central del procesamiento. Usa la sesión db recibida como parámetro,
    lo que permite inyectar una sesión de test sin tocar el ciclo HTTP.
    """
    process_repository.update_process_status(
        db=db,
        process_id=process_id,
        status=ProcessStatus.RUNNING.value,
    )

    process_repository.add_activity_log(
        db=db,
        process_id=process_id,
        message="Process started in background",
    )

    result_data = process_documents()

    process_repository.update_process_progress(
        db=db,
        process_id=process_id,
        processed_files=result_data["processed_files"],
        total_files=result_data["total_files"],
    )

    result = ProcessResult(
        process_id=process_id,
        total_words=result_data["total_words"],
        total_lines=result_data["total_lines"],
        total_characters=result_data["total_characters"],
        most_frequent_words=json.dumps(result_data["most_frequent_words"]),
        files_processed=json.dumps(result_data["files_processed"]),
        summary=result_data["summary"],
    )

    process_repository.save_process_result(db, result)

    process_repository.update_process_status(
        db=db,
        process_id=process_id,
        status=ProcessStatus.COMPLETED.value,
    )

    process_repository.add_activity_log(
        db=db,
        process_id=process_id,
        message="Process completed successfully",
    )


def run_process_in_background(process_id: str) -> None:
    """
    Ejecuta el procesamiento de documentos en segundo plano.

    Importante:
    - No reutilizo la sesión del endpoint.
    - Creo una sesión nueva porque este código corre fuera del ciclo HTTP.
    """
    db = SessionLocal()

    try:
        _execute_process(process_id, db)
    except Exception as exc:
        process_repository.update_process_status(
            db=db,
            process_id=process_id,
            status=ProcessStatus.FAILED.value,
            error_message=str(exc),
        )

        process_repository.add_activity_log(
            db=db,
            process_id=process_id,
            message=f"Process failed: {str(exc)}",
            level="ERROR",
        )

    finally:
        db.close()


def list_process_logs(db: Session, process_id: str):
    process = process_repository.get_process_by_id(db, process_id)

    if process is None:
        return None

    return process_repository.list_activity_logs(db, process_id)     

