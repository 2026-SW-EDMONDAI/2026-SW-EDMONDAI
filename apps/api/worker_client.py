"""Thin wrapper for publishing tasks to Celery from the API."""
import os

from celery import Celery

_broker_user = os.getenv("RABBITMQ_USER", "guest")
_broker_pass = os.getenv("RABBITMQ_PASSWORD", "guest")
_broker_host = os.getenv("RABBITMQ_HOST", "localhost")
_broker_port = os.getenv("RABBITMQ_PORT", "5672")

_celery = Celery(
    broker=f"amqp://{_broker_user}:{_broker_pass}@{_broker_host}:{_broker_port}//",
)


def publish_analyze_video(video_id: str) -> None:
    _celery.send_task(
        "worker.tasks.video_processing.analyze_video",
        args=[video_id],
        queue="video-processing",
    )
