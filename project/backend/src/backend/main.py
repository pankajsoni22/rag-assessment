from fastapi import FastAPI

app = FastAPI(title="RAG Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
