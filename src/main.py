"""
Pocket Nori API — application entry point.

Instantiates the FastAPI app, registers middleware, and mounts all routers.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.api.routes import router
from src.config import settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CSRF Origin validation middleware
# ---------------------------------------------------------------------------

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _extract_origin(url: str) -> str:
    """Return scheme://host from a full URL."""
    parts = urlsplit(url)
    if parts.scheme and parts.netloc:
        return f"{parts.scheme}://{parts.netloc}"
    return ""


def _allowed_origins() -> set[str]:
    """Build the set of trusted origins for CSRF validation."""
    origins = {settings.frontend_origin}
    if settings.API_BASE_URL:
        origins.add(_extract_origin(settings.API_BASE_URL))
    origins.discard("")
    return origins


class CSRFOriginMiddleware(BaseHTTPMiddleware):
    """Reject mutating requests from unknown origins when a session cookie is present.

    Rules:
    1. Safe methods (GET, HEAD, OPTIONS) always pass through.
    2. On mutating methods (POST, PUT, PATCH, DELETE):
       - If no session cookie → allow (bearer-token or unauthenticated requests).
       - If session cookie AND Origin header → validate against allowlist.
       - If session cookie AND no Origin but Referer → extract origin from Referer, validate.
       - If session cookie AND neither Origin nor Referer → reject with 403.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if request.method in _SAFE_METHODS:
            response: Response = await call_next(request)
            return response

        # Only enforce CSRF for cookie-authenticated requests
        if "session" not in request.cookies:
            response = await call_next(request)
            return response

        allowed = _allowed_origins()

        # Check Origin header first
        origin = request.headers.get("origin")
        if origin:
            if _extract_origin(origin) in allowed:
                response = await call_next(request)
                return response
            logger.warning("CSRF rejected: Origin %s not in allowlist", origin)
            return JSONResponse(
                status_code=403,
                content={"detail": "Origin not allowed"},
            )

        # Fall back to Referer header
        referer = request.headers.get("referer")
        if referer:
            referer_origin = _extract_origin(referer)
            if referer_origin in allowed:
                response = await call_next(request)
                return response
            logger.warning("CSRF rejected: Referer origin %s not in allowlist", referer_origin)
            return JSONResponse(
                status_code=403,
                content={"detail": "Origin not allowed"},
            )

        # No Origin, no Referer — reject
        logger.warning("CSRF rejected: no Origin or Referer header on mutating request")
        return JSONResponse(
            status_code=403,
            content={"detail": "Origin header required for mutating requests"},
        )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info("Pocket Nori API starting up")
    yield
    logger.info("Pocket Nori API shutting down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Pocket Nori API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — only the configured frontend origin is allowed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSRF Origin validation — registered after CORS so it runs first on requests
app.add_middleware(CSRFOriginMiddleware)

# Routers
app.include_router(router)
