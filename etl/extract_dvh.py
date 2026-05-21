"""DVH extraction from RTSTRUCT and RTDOSE objects."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

DVH_METRIC_NAMES: Tuple[str, ...] = ("Dmean", "Dmax", "Dmin", "D95", "V5", "V10", "V20", "V30", "V40", "V50")


@dataclass(frozen=True)
class DvhMetric:
    """One dose-volume histogram metric for one ROI."""

    roi_name: str
    metric_name: str
    metric_value: float
    metric_unit: str


def extract_dvh_metrics(rtstruct_path: Path, rtdose_path: Path) -> List[DvhMetric]:
    """Extract basic DVH metrics using dicompyler-core when available."""

    try:
        from dicompylercore import dicomparser, dvhcalc
    except ImportError:
        logger.warning("dicompyler-core is unavailable; skipping DVH extraction")
        return []

    try:
        structure_parser = dicomparser.DicomParser(str(rtstruct_path))
        structures: Dict[int, Dict[str, Any]] = structure_parser.GetStructures()
        metrics: List[DvhMetric] = []
        for roi_number, roi in structures.items():
            roi_name = str(roi.get("name") or f"ROI_{roi_number}")
            dvh = dvhcalc.get_dvh(str(rtstruct_path), str(rtdose_path), roi_number)
            if dvh is None:
                continue
            metrics.extend(_metrics_from_dvh(roi_name, dvh))
        return metrics
    except Exception as exc:
        logger.exception("DVH extraction failed for %s and %s: %s", rtstruct_path, rtdose_path, exc)
        return []


def _metrics_from_dvh(roi_name: str, dvh: Any) -> List[DvhMetric]:
    """Convert a dicompyler DVH object into the warehouse metric set."""

    rows: List[DvhMetric] = []
    dose_unit = "Gy"
    volume_unit = "%"

    for name, attr in (("Dmean", "mean"), ("Dmax", "max"), ("Dmin", "min")):
        value = getattr(dvh, attr, None)
        if value is not None:
            rows.append(DvhMetric(roi_name, name, float(value), dose_unit))

    try:
        rows.append(DvhMetric(roi_name, "D95", float(dvh.statistic("D95").value), dose_unit))
    except Exception:
        logger.debug("D95 unavailable for ROI %s", roi_name)

    for dose in (5, 10, 20, 30, 40, 50):
        try:
            rows.append(DvhMetric(roi_name, f"V{dose}", float(dvh.statistic(f"V{dose}Gy").value), volume_unit))
        except Exception:
            logger.debug("V%s unavailable for ROI %s", dose, roi_name)

    return rows
