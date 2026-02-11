from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ImportError, ImportJob
from app.db.session import get_db
from app.schemas.import_schema import ImportErrorItem, ImportJobResponse, ImportResult
from app.services.excel_service import (
    parse_excel_bytes,
    validate_and_transform_rows,
    validate_required_columns,
)
from app.services.import_service import (
    create_job,
    finalize_job,
    save_validation_errors,
    set_job_failed,
    upsert_sales_records,
)

router = APIRouter(prefix="/imports", tags=["imports"])
settings = get_settings()


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.post("/upload", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
async def upload_excel(
    request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)
) -> ImportResult:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension {ext or 'unknown'} is not allowed.",
        )

    raw_bytes = await file.read()
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(raw_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is too large. Max size is {settings.max_upload_size_mb} MB.",
        )

    correlation_id = getattr(request.state, "correlation_id", str(uuid4()))
    job = create_job(db=db, filename=file.filename or "unknown.xlsx", correlation_id=correlation_id)

    try:
        frame = parse_excel_bytes(raw_bytes)
    except Exception as exc:  # noqa: BLE001
        set_job_failed(db, job, f"Failed to parse excel file: {exc}")
        raise HTTPException(status_code=400, detail="Invalid Excel file.") from exc

    missing_columns = validate_required_columns(frame)
    if missing_columns:
        msg = f"Missing required columns: {', '.join(missing_columns)}"
        set_job_failed(db, job, msg)
        return ImportResult(
            job_id=job.id,
            status=job.status,
            filename=job.filename,
            total_rows=0,
            imported_rows=0,
            failed_rows=0,
            message=msg,
            errors=[],
        )

    valid_rows, validation_errors = validate_and_transform_rows(frame)
    save_validation_errors(db, job.id, validation_errors)
    imported_rows = upsert_sales_records(db, valid_rows) if valid_rows else 0
    total_rows = len(frame)
    failed_rows = len({item.row_number for item in validation_errors})
    updated = finalize_job(
        db,
        job,
        total_rows=total_rows,
        imported_rows=imported_rows,
        failed_rows=failed_rows,
        message="Import finished",
    )

    return ImportResult(
        job_id=updated.id,
        status=updated.status,
        filename=updated.filename,
        total_rows=updated.total_rows,
        imported_rows=updated.imported_rows,
        failed_rows=updated.failed_rows,
        message=updated.message,
        errors=[
            ImportErrorItem(
                row_number=item.row_number,
                column_name=item.column_name,
                error_message=item.error_message,
            )
            for item in validation_errors
        ],
    )


@router.get("/{job_id}", response_model=ImportJobResponse)
def get_import_job(job_id: int, db: Session = Depends(get_db)) -> ImportJobResponse:
    job = db.get(ImportJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return ImportJobResponse.model_validate(job)


@router.get("/{job_id}/errors", response_model=list[ImportErrorItem])
def get_import_errors(job_id: int, db: Session = Depends(get_db)) -> list[ImportErrorItem]:
    job = db.get(ImportJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    rows = db.query(ImportError).filter(ImportError.job_id == job_id).all()
    return [
        ImportErrorItem(
            row_number=item.row_number,
            column_name=item.column_name,
            error_message=item.error_message,
        )
        for item in rows
    ]
