from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ImportError, ImportJob, SalesRecord
from app.services.excel_service import ValidationErrorItem


def create_job(db: Session, filename: str, correlation_id: str) -> ImportJob:
    job = ImportJob(
        filename=filename,
        correlation_id=correlation_id,
        status="running",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def set_job_failed(db: Session, job: ImportJob, message: str) -> ImportJob:
    job.status = "failed"
    job.message = message
    db.commit()
    db.refresh(job)
    return job


def save_validation_errors(
    db: Session, job_id: int, errors: list[ValidationErrorItem]
) -> None:
    if not errors:
        return
    db.add_all(
        [
            ImportError(
                job_id=job_id,
                row_number=error.row_number,
                column_name=error.column_name,
                error_message=error.error_message,
            )
            for error in errors
        ]
    )
    db.commit()


def upsert_sales_records(db: Session, rows: list[dict[str, Any]]) -> int:
    imported = 0
    updatable_fields = [
        "name",
        "amount",
        "record_date",
        "invoice_date",
        "invoice_no",
        "item_description",
        "product_value",
        "tax_value",
        "total_value",
        "vin_no",
        "cancel_flag",
        "cancel_product_value",
        "cancel_tax_value",
        "cancel_total_value",
        "org_type_hq",
        "org_type_branch_no",
        "taxpayer_id",
        "sale_price",
        "com_fn",
        "com_value",
        "rule_applied",
        "is_duplicate_tank",
        "group_id",
    ]
    for row in rows:
        existing = db.scalar(
            select(SalesRecord).where(SalesRecord.business_key == row["business_key"])
        )
        if existing is None:
            db.add(SalesRecord(**row))
        else:
            for field_name in updatable_fields:
                setattr(existing, field_name, row.get(field_name))
        imported += 1
    db.commit()
    return imported


def finalize_job(
    db: Session,
    job: ImportJob,
    total_rows: int,
    imported_rows: int,
    failed_rows: int,
    message: str | None = None,
) -> ImportJob:
    job.total_rows = total_rows
    job.imported_rows = imported_rows
    job.failed_rows = failed_rows
    job.status = "success" if failed_rows == 0 else "completed_with_errors"
    job.message = message
    db.commit()
    db.refresh(job)
    return job
