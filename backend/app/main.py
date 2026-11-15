"""
FastAPI Application Entry Point for EduHyper-RAG Backend.
Configures CORS, registers API routers, sets up global error handling without secret leakage,
and mounts interactive Swagger / OpenAPI documentation.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.courses import router as courses_router
from backend.app.api.documents import router as documents_router
from backend.app.api.tutor import router as tutor_router
from backend.app.api.hypergraph import router as hypergraph_router
from backend.app.api.analytics import router as analytics_router
from backend.app.core.config import settings
from src.utils.logger import get_logger

logger = get_logger("fastapi_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for startup and shutdown procedures."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version} [{settings.app_env.upper()}]")
    yield
    logger.info(f"Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    """Application factory for FastAPI instance."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "EduHyper-RAG Backend API: High-order hypergraph-driven educational tutor "
            "with agentic verification and hallucination reduction."
        ),
        docs_url="/docs" if not settings.is_production() else None,
        redoc_url="/redoc" if not settings.is_production() else None,
        openapi_url="/openapi.json" if not settings.is_production() else None,
        lifespan=lifespan,
    )

    # =========================================================================
    # CORS Configuration
    # =========================================================================
    # In development: allows localhost:5173 (React Vite frontend)
    # In production: restricted strictly to configured origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins if isinstance(settings.cors_origins, list) else [settings.cors_origins],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )

    # =========================================================================
    # Exception Handlers (Prevent stack traces & secrets from leaking to clients)
    # =========================================================================

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation error in request payload.", "errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # Log complete stack trace internally for developers
        logger.exception(f"Unhandled server exception on {request.method} {request.url.path}: {str(exc)}")
        # Return sanitized error message to the client (no tracebacks or environment variables)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please contact the administrator."},
        )

    # =========================================================================
    # Route Registration
    # =========================================================================
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=f"{settings.api_prefix}/auth", tags=["Authentication"])
    app.include_router(courses_router, prefix=f"{settings.api_prefix}/courses", tags=["Courses"])
    app.include_router(documents_router, prefix=f"{settings.api_prefix}/documents", tags=["Documents"])
    app.include_router(tutor_router, prefix=f"{settings.api_prefix}/tutor", tags=["AI Tutor"])
    app.include_router(hypergraph_router, prefix=f"{settings.api_prefix}/hypergraph", tags=["Hypergraph Explorer"])
    app.include_router(analytics_router, prefix=f"{settings.api_prefix}/analytics", tags=["Analytics & Progress"])

    @app.get("/", tags=["Root"])
    def root():
        """Root welcome redirect / status."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs" if not settings.is_production() else "Disabled in production",
            "health": f"{settings.api_prefix}/health",
        }

    return app


# Application instance for Uvicorn
app = create_app()
