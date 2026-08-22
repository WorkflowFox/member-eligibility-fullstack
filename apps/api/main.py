"""FastAPI application entrypoint for the api service.

This module holds the single FastAPI app instance that later endpoints
(e.g. the eligibility check) will be added to. Run locally with:

    uvicorn main:app --reload
"""

from fastapi import FastAPI

app = FastAPI(title="Member Eligibility API")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Does not depend on the database."""
    return {"status": "ok"}
