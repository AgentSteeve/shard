"""FastAPI app — web UI + JSON API over the shard index."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from shard.config import APP_NAME, APP_VERSION, DEFAULT_LIMIT
from shard.db import init
from shard.search import export_csv, search_domain, search_email, stats

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

app = FastAPI(title=APP_NAME, version=APP_VERSION)


@app.on_event("startup")
async def _startup():
    init()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, q: str = "", exact: int = 0, limit: int = DEFAULT_LIMIT):
    rows = []
    if q.strip():
        rows = search_email(q, limit=limit, exact=bool(exact))
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "q": q,
            "exact": exact,
            "limit": limit,
            "rows": rows,
            "stats": stats(),
        },
    )


@app.get("/api/search")
async def api_search(q: str, exact: int = 0, limit: int = DEFAULT_LIMIT):
    rows = search_email(q, limit=limit, exact=bool(exact))
    return JSONResponse({"query": q, "count": len(rows), "results": rows})


@app.get("/api/domain")
async def api_domain(d: str, limit: int = DEFAULT_LIMIT):
    rows = search_domain(d, limit=limit)
    return JSONResponse({"domain": d, "count": len(rows), "results": rows})


@app.get("/api/stats")
async def api_stats():
    return JSONResponse(stats())


@app.get("/export", response_class=PlainTextResponse)
async def export(q: str, exact: int = 0, limit: int = 500):
    rows = search_email(q, limit=limit, exact=bool(exact))
    return export_csv(rows)


@app.get("/health")
async def health():
    return {"status": "ok", "app": APP_NAME, "version": APP_VERSION}
