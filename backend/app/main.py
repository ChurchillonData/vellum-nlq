from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.data_window import rolling_data_window


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type"],
        )

    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, object]:
        window = rolling_data_window(
            as_of_date=settings.demo_as_of_date,
            month_count=settings.demo_month_count,
        )
        return {
            "status": "ok",
            "catalogue": settings.active_catalogue,
            "data_window": {
                "as_of_date": window.as_of_date.isoformat(),
                "start_date": window.start_date.isoformat(),
                "end_date": window.end_date.isoformat(),
                "month_count": window.month_count,
            },
        }

    return app


app = create_app()
