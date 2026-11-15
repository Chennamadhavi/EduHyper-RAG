"""
Health Check and Subsystem Status API Router.
Provides GET /api/health returning verified operational states of backend services
without executing expensive LLM generation or vector embedding calls.
"""

from fastapi import APIRouter, status
from backend.app.core.config import settings
from backend.app.schemas import ComponentStatus, HealthResponse
from backend.app.services.pipeline_adapter import pipeline_adapter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Service Health Status",
    description="Returns API service health, active environment, and non-destructive subsystem status.",
)
def get_health() -> HealthResponse:
    """
    Returns system status and inspects storage/configuration read-only.
    Never calls external LLMs or performs vector queries during this check.
    """
    raw_subsystems = pipeline_adapter.inspect_subsystems()

    components = {
        name: ComponentStatus(status=info["status"], detail=info["detail"])
        for name, info in raw_subsystems.items()
    }

    # API itself is healthy if this endpoint responds
    components["api"] = ComponentStatus(
        status="healthy",
        detail="FastAPI application router active and responding.",
    )

    # Determine overall status
    is_degraded = any(c.status == "error" for c in components.values())
    overall_status = "degraded" if is_degraded else "ok"

    return HealthResponse(
        status=overall_status,
        app_name=settings.app_name,
        environment=settings.app_env,
        version=settings.app_version,
        components=components,
    )
