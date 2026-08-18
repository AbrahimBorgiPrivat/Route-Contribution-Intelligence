import pytest
import requests

def skip_if_service_unavailable(
    url: str,
    *,
    timeout: float = 0.5,
    reason: str | None = None,
    ) -> None:
    """
    Skip test if an HTTP service is not reachable.
    """
    try:
        requests.get(url, timeout=timeout)
    except Exception:
        pytest.skip(
            reason
            or f"Service not available: {url}"
        )
