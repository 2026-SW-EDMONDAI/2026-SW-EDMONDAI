import os

from celery import Celery

broker_user = os.getenv("RABBITMQ_USER", "guest")
broker_pass = os.getenv("RABBITMQ_PASSWORD", "guest")
broker_host = os.getenv("RABBITMQ_HOST", "localhost")
broker_port = os.getenv("RABBITMQ_PORT", "5672")

app = Celery(
    "worker",
    broker=f"amqp://{broker_user}:{broker_pass}@{broker_host}:{broker_port}//",
)

app.conf.task_queues = {
    "default": {},
    "video-processing": {},
    "metrics-aggregation": {},
    "recommendation": {},
}
