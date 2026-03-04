"""FastAPI application factory and health endpoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analytics_router import analytics_router
from app.api.metrics_router import metrics_router
from app.api.athlete_router import athlete_router
from app.api.health_data_router import router as health_data_router
from app.api.coach_router import coach_router
from app.api.session_router import router as session_router
from app.api.sync_router import router as sync_router
from app.api.team_router import team_router
from app.api.wellness_router import router as wellness_router
from app.auth.router import router as auth_router
from app.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Wearable Athlete Monitoring Platform",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth_router)
    app.include_router(team_router)
    app.include_router(athlete_router)
    app.include_router(coach_router)
    app.include_router(session_router)
    app.include_router(wellness_router)
    app.include_router(sync_router)
    app.include_router(health_data_router)
    app.include_router(analytics_router)
    app.include_router(metrics_router)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()
