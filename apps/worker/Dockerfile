FROM python:3.13-slim

WORKDIR /app

COPY ../api/pyproject.toml /deps/pyproject.toml
RUN pip install --no-cache-dir -e /deps

COPY . .

CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "-Q", "default,video-processing,metrics-aggregation,recommendation"]
