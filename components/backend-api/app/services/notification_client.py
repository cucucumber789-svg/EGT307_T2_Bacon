"""HTTP client for the Notification microservice."""

import logging

import requests

from app.config import Config

logger = logging.getLogger(__name__)


def notify_anomaly(payload):
    """Best-effort POST of one anomalous reading to the notification service.

    Never raises: an alert is not worth failing the prediction that found it.
    Returns the parsed response, or None if the service is unavailable.
    """
    try:
        resp = requests.post(
            f"{Config.NOTIFICATION_SERVICE_URL}/api/notify",
            json=payload,
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.warning("Notification service unavailable: %s", e)
        return None
