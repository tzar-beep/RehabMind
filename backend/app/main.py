import asyncio
import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.admin.router import router as admin_router
from app.ai.clinician_router import router as ai_clinician_router
from app.ai.clinician_router import status_router as ai_status_router
from app.ai.provider import get_ai_provider
from app.ai.router import router as ai_router
from app.auth.router import router as auth_router
from app.clinical.router import options_router as clinical_options_router
from app.clinical.router import router as clinical_router
from app.clinicians.patient_router import router as clinician_patient_router
from app.clinicians.router import router as clinicians_router
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_var
from app.health.router import router as health_router
from app.patients.router import router as patients_router
from app.sessions.router import router as practice_router
from app.speech.router import router as speech_router

configure_logging()
settings = get_settings()
log = logging.getLogger("app")
access_log = logging.getLogger("app.access")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Load the local LLM in the background; requests before it is ready fall back safely.
    provider = get_ai_provider()
    task = None
    if hasattr(provider, "warm_up"):
        task = asyncio.create_task(provider.warm_up())
    yield
    if task is not None and not task.done():
        task.cancel()


app = FastAPI(
    lifespan=lifespan,
    title="RehabMind",
    docs_url=None if settings.is_production else "/api/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/api/openapi.json",
)

api = APIRouter(prefix="/api/v1")
for r in (
    auth_router,
    clinical_router,
    clinical_options_router,
    ai_router,
    ai_status_router,
    ai_clinician_router,
    patients_router,
    clinicians_router,
    clinician_patient_router,
    practice_router,
    speech_router,
    admin_router,
):
    api.include_router(r)
app.include_router(api)
app.include_router(health_router, prefix="/api")

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_allowed_origins = {o.rstrip("/") for o in settings.frontend_origins}


def _origin_allowed(request: Request) -> bool:
    """CSRF defence (with SameSite=Lax): unsafe requests must come from our own frontend."""
    origin = request.headers.get("origin")
    if origin is None and (referer := request.headers.get("referer")):
        p = urlparse(referer)
        origin = f"{p.scheme}://{p.netloc}"
    return origin is not None and origin.rstrip("/") in _allowed_origins


@app.middleware("http")
async def security_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    rid = uuid.uuid4().hex
    request_id_var.set(rid)
    started = time.perf_counter()
    if request.method in UNSAFE_METHODS and not _origin_allowed(request):
        response: Response = JSONResponse({"detail": "Request origin not allowed."}, 403)
    else:
        try:
            response = await call_next(request)
        except Exception:
            log.exception("unhandled error")
            response = JSONResponse({"detail": "Something went wrong."}, 500)
    # Route template only (e.g. /api/v1/patients/{patient_id}): no IDs, no query strings.
    route = request.url.path
    for name, value in request.path_params.items():
        route = route.replace(str(value), "{" + name + "}")
    access_log.info(
        "request",
        extra={
            "data": {
                "method": request.method,
                "route": route if "route" in request.scope else "unmatched",
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        },
    )
    response.headers["X-Request-ID"] = rid
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    return response


# Explicit origins only; never a wildcard with credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(_allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)
