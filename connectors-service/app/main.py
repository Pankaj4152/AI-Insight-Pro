from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CORS_ORIGINS, CORS_CREDENTIALS, CORS_METHODS, CORS_HEADERS
from app.routers import validation, model_inventory, general


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Connectors API",
        description="API for managing database connections and model inventory",
        version="1.0.0"
    )

    # CORS setup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=CORS_CREDENTIALS,
        allow_methods=CORS_METHODS,
        allow_headers=CORS_HEADERS,
    )

    # Include routers
    app.include_router(validation.router)
    app.include_router(model_inventory.router)
    app.include_router(general.router)

    @app.get("/")
    async def root():
        return {"message": "Connectors API is running"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


# Create the app instance
app = create_app()
