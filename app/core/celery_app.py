"""Celery application configuration for ProofStack.

Broker and backend: Redis (configurable via REDIS_URL env var).

Start worker (development):
    celery -A app.core.celery_app worker --loglevel=info --pool=solo

Start worker (production):
    celery -A app.core.celery_app worker --loglevel=info --concurrency=4 --pool=prefork
"""

from __future__ import annotations

import os

from celery import Celery

_redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "proofstack",
    broker=_redis_url,
    backend=_redis_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Ack on delivery (not late) — if the worker crashes, the DB row
    # stays as RUNNING/PENDING which the user can re-trigger.  Avoids
    # "invisible" tasks that sit unacked in Redis after restarts.
    task_acks_late=False,
    task_reject_on_worker_lost=False,
    # Prefetch only 1 task at a time (prevents solo pool from hoarding
    # messages it can't process concurrently).
    worker_prefetch_multiplier=1,
    # Recycle worker after 50 tasks to prevent leaks
    worker_max_tasks_per_child=50,
    # Task time limit (5 minutes hard, 4 minutes soft)
    task_soft_time_limit=240,
    task_time_limit=300,
    # Result expiry: 1 hour (results live in Redis)
    result_expires=3600,
    # Broker connection retry on startup
    broker_connection_retry_on_startup=True,
)
