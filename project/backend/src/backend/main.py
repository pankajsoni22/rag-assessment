from fastapi import FastAPI

from backend.api import document_routes, query_routes, set_routes

app = FastAPI(title="RAG Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(set_routes.router)
app.include_router(document_routes.router)
app.include_router(query_routes.router)
