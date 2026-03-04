"""Celery beat schedule configuration."""


from app.config import settings


def get_beat_schedule() -> dict:  # type: ignore[type-arg]
    """Return the Celery beat schedule dictionary."""
    return {
        "sync-all-athletes": {
            "task": "app.tasks.sync_tasks.sync_all_athletes_task",
            "schedule": settings.SYNC_INTERVAL_MINUTES * 60.0,  # seconds
            "options": {"queue": "sync"},
        },
    }
