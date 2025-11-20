from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routes import clients, pages, scrapes


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="IG Follower Analyzer API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(clients.router, prefix=settings.api_prefix)
    app.include_router(pages.router, prefix=settings.api_prefix)
    app.include_router(scrapes.router, prefix=settings.api_prefix)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

