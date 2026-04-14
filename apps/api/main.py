from fastapi import FastAPI

from core.config import settings
from core.exceptions import AppException, app_exception_handler, unhandled_exception_handler
from core.middleware import RequestIdMiddleware
from routes.health import router as health_router

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Middleware
app.add_middleware(RequestIdMiddleware)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Routers
app.include_router(health_router)
