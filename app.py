"""Customer 360 Databricks App — FastAPI entrypoint.

- Serves REST API under /api/*
- Serves the React SPA built into frontend/dist
- /docs  — interactive Swagger for the REST API
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from server.routes import router as api_router

app = FastAPI(
    title="Customer 360 — Fintech BNPL",
    description=(
        "Consolidated customer 360 view across four BNPL sales channels "
        "(mobile app, partner checkout, web portal, co-branded card). "
        "Same data is reachable programmatically via this REST API and "
        "interactively via the bundled UI."
    ),
    version="1.0.0",
)

app.include_router(api_router, prefix="/api")


@app.exception_handler(Exception)
async def _unhandled(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# --- Static frontend ---------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.isdir(FRONTEND_DIR):
    assets_dir = os.path.join(FRONTEND_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        if full_path.startswith("api/"):
            # Let API 404s come from the router rather than serving index.html.
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
else:

    @app.get("/", include_in_schema=False)
    async def root():
        return JSONResponse(
            {
                "message": "Frontend not built. Run `cd frontend && npm run build`.",
                "api_docs": "/docs",
            }
        )
