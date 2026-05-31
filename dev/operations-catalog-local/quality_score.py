import os
import logging
import requests
from dotenv import load_dotenv
load_dotenv()

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from database import get_db

PROMETHEUS_PUSHGATEWAY_URL = os.environ.get("PROMETHEUS_PUSHGATEWAY_URL", "")

logger = logging.getLogger(__name__)

if not PROMETHEUS_PUSHGATEWAY_URL:
    logger.warning("PROMETHEUS_PUSHGATEWAY_URL is not set; quality score pushes will be skipped")

STATUS_SCORE_MAP = {
    "ok": 1.0, "healthy": 1.0, "operational": 1.0, "up": 1.0, "green": 1.0,
    "degraded": 0.5, "warning": 0.5, "partial_outage": 0.5, "yellow": 0.5,
    "down": 0.0, "error": 0.0, "critical": 0.0, "major_outage": 0.0, "red": 0.0,
}


def fetch_and_push_quality_score(service_name: str, url: str):
    """Fetch JSON status from url, map to 0-1 score, push to Pushgateway.

    Returns the score (float) on success, None on any failure (no push on failure).
    """
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        status = data["status"].lower()
        score = STATUS_SCORE_MAP.get(status, 0.0)
        registry = CollectorRegistry()
        gauge = Gauge(
            "service_quality_score",
            "Quality score derived from service status page (0=down, 1=healthy)",
            labelnames=["service"],
            registry=registry,
        )
        gauge.labels(service=service_name).set(score)
        push_to_gateway(PROMETHEUS_PUSHGATEWAY_URL, job="quality_scores", registry=registry)
        return score
    except Exception as e:
        logger.warning("Failed to fetch/push quality score for %s: %s", service_name, e)
        return None


def refresh_all_quality_scores(app):
    """Query all catalog entries with a statusPageUrl and refresh their quality scores.

    Called by the APScheduler background job. Runs inside a Flask app context so
    get_db() (which uses Flask's g) works correctly.
    """
    with app.app_context():
        try:
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT "serviceName", "statusPageUrl" FROM catalog '
                    'WHERE "statusPageUrl" IS NOT NULL AND "statusPageUrl" != \'\''
                )
                rows = cur.fetchall()
            for service_name, url in rows:
                try:
                    fetch_and_push_quality_score(service_name, url)
                except Exception as e:
                    logger.warning("Error refreshing quality score for %s: %s", service_name, e)
        except Exception as e:
            logger.warning("Error in refresh_all_quality_scores: %s", e)


def start_scheduler(app):
    """Start the APScheduler background job for quality score refresh.

    Call this from app.py's __main__ block. Registers an atexit handler to shut
    the scheduler down cleanly when Flask exits.

    NOTE: This only runs when Flask's built-in dev server is used directly.
    For production deployments (gunicorn, uwsgi), wire start_scheduler() into
    the app factory or a custom server entrypoint.
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    import atexit
    interval = int(os.environ.get("QUALITY_SCORE_INTERVAL_MINUTES", "10"))
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: refresh_all_quality_scores(app),
        "interval",
        minutes=interval,
    )
    scheduler.start()
    atexit.register(scheduler.shutdown)
    logger.info("Quality score scheduler started (interval: %d minutes)", interval)
