from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "catalogue": settings.active_catalogue,
        }

    return app


app = create_app()
