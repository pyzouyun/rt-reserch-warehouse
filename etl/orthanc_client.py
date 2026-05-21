"""Small Orthanc REST API client."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests
from requests import Session

from etl.config import get_settings

logger = logging.getLogger(__name__)


class OrthancClient:
    """Client for reading studies, series, and instances from Orthanc."""

    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.orthanc_url).rstrip("/")
        self.session: Session = requests.Session()
        self.session.auth = (username or settings.orthanc_username, password or settings.orthanc_password)

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        response = self.session.request(method, url, timeout=60, **kwargs)
        response.raise_for_status()
        return response

    def list_instances(self) -> List[str]:
        """Return all Orthanc instance identifiers."""

        return list(self._request("GET", "/instances").json())

    def get_instance_file(self, instance_id: str) -> bytes:
        """Download a DICOM instance as bytes."""

        return self._request("GET", f"/instances/{instance_id}/file").content

    def get_instance_tags(self, instance_id: str) -> Dict[str, Any]:
        """Return simplified tags for an instance."""

        return dict(self._request("GET", f"/instances/{instance_id}/simplified-tags").json())

    def healthcheck(self) -> bool:
        """Return whether Orthanc responds to the system endpoint."""

        try:
            self._request("GET", "/system")
            return True
        except requests.RequestException as exc:
            logger.error("Orthanc healthcheck failed: %s", exc)
            return False
