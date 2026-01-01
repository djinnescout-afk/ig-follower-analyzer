from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routes import clients, pages, scrapes, outreach


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="IG Follower Analyzer API", version="0.1.0")

    # CORS configuration - uses CORS_ORIGINS env var, defaults to ["*"] for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_origins != ["*"],  # Only allow credentials if not wildcard
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )

    app.include_router(clients.router, prefix=settings.api_prefix)
    app.include_router(pages.router, prefix=settings.api_prefix)
    app.include_router(scrapes.router, prefix=settings.api_prefix)
    app.include_router(outreach.router, prefix=settings.api_prefix)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

