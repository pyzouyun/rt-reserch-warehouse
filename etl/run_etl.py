"""Main ETL entry point for scanning Orthanc and loading PostgreSQL."""

from __future__ import annotations

from io import BytesIO
import logging
import sys

import pydicom

from etl.config import get_settings
from etl.db import db_connection
from etl.load_to_db import log_etl_event, promote_contextual_planning_ct, upsert_parsed_dicom
from etl.orthanc_client import OrthancClient
from etl.parse_dicom import parse_dataset


def configure_logging() -> None:
    """Configure process logging from environment settings."""

    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def run() -> int:
    """Scan all Orthanc instances and upsert supported metadata."""

    configure_logging()
    logger = logging.getLogger(__name__)
    settings = get_settings()
    client = OrthancClient()

    processed = 0
    try:
        instance_ids = client.list_instances()
        logger.info("Found %s Orthanc instances", len(instance_ids))
        with db_connection() as connection:
            for instance_id in instance_ids:
                try:
                    payload = client.get_instance_file(instance_id)
                    dataset = pydicom.dcmread(BytesIO(payload), force=True, stop_before_pixels=True)
                    parsed = parse_dataset(dataset, salt=settings.deidentify_salt, orthanc_instance_id=instance_id)
                    upsert_parsed_dicom(connection, parsed)
                    processed += 1
                except Exception as exc:
                    logger.exception("Failed to process Orthanc instance %s: %s", instance_id, exc)
            promoted = promote_contextual_planning_ct(connection)
            log_etl_event(
                connection,
                pipeline_name="orthanc_dicom_scan",
                status="success",
                message=(
                    f"Processed {processed} of {len(instance_ids)} Orthanc instances; "
                    f"promoted {promoted} CT series by RT study context"
                ),
                records_processed=processed,
            )
        return 0
    except Exception as exc:
        logger.exception("ETL failed: %s", exc)
        try:
            with db_connection() as connection:
                log_etl_event(
                    connection,
                    pipeline_name="orthanc_dicom_scan",
                    status="failed",
                    message=str(exc),
                    records_processed=processed,
                )
        except Exception:
            logger.exception("Could not write ETL failure log")
        return 1


if __name__ == "__main__":
    sys.exit(run())
