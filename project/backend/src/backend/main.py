import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api import document_routes, query_routes, set_routes
from backend.api.dependencies import get_settings

logger = logging.getLogger("backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_settings()
    except Exception as exc:
        logger.warning(
            "Startup configuration check failed — requests will error until this is fixed "
            "(check .env for GROQ_API_KEY, GOOGLE_API_KEY, CHROMA_PERSIST_DIR): %s",
            exc,
        )
    yield


app = FastAPI(title="RAG Backend", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(set_routes.router)
app.include_router(document_routes.router)
app.include_router(query_routes.router)
