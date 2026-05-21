"""Health endpoints."""

from fastapi import APIRouter
from typing import Dict

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> Dict[str, str]:
    """Return API health status."""

    return {"status": "ok", "service": "rt-research-api"}
