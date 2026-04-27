from fastapi import FastAPI

from core.config import settings
from core.exceptions import AppException, app_exception_handler, unhandled_exception_handler
from core.logging import setup_logging
from core.metrics import instrumentator
from core.middleware import RequestIdMiddleware
from routes.auth import router as auth_router
from routes.health import router as health_router

# Initialize structured logging
setup_logging()

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Middleware
app.add_middleware(RequestIdMiddleware)

# Prometheus metrics — exposes /metrics endpoint
instrumentator.instrument(app).expose(app, include_in_schema=False)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Routers
app.include_router(health_router)
app.include_router(auth_router)
