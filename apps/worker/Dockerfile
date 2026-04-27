FROM python:3.13-slim

WORKDIR /app

COPY apps/api /deps
RUN pip install --no-cache-dir /deps

COPY apps/worker /app

CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "-Q", "default,video-processing,metrics-aggregation,recommendation"]
