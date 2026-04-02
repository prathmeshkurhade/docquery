from celery import Celery

from app.config import settings

# Create Celery instance
# - "app.workers" is just a name for logging/debugging
# - broker = Redis (where task messages are stored)
# - backend = Redis (where task results/status are stored)
celery_app = Celery(
    "app.workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configuration
celery_app.conf.update(
    # Serialize task arguments as JSON (not pickle — pickle is a security risk)
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # UTC timezone for consistent timestamps
    timezone="UTC",
    enable_utc=True,

    # Auto-discover tasks in these modules
    # Celery will look for functions decorated with @celery_app.task
    imports=["app.workers.pdf_pipeline"],
)
