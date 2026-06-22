import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.core.codes import ErrorCode
from app.core.exceptions import AppException
from app.core.logging import logger
from app.domains.auth.router import router as auth_router
from app.domains.directions.router import router as directions_router
from app.domains.fiches_de_poste.router import router as fiches_de_poste_router
from app.domains.offres.router import router as offres_router
from app.domains.recruitment.router import (
    besoins_router as recruitment_besoins_router,
)
from app.domains.recruitment.router import (
    router as recruitment_router,
)
from app.domains.users.router import router as users_router

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    logger.info(
        "method=%s path=%s status=%s duration=%sms",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response

# ---------------------------------------------------------------------------
# Exception handlers — uniform response {"detail", "code", "status"}
# ---------------------------------------------------------------------------
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code, "status": exc.status_code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": jsonable_encoder(exc.errors()),
            "code": ErrorCode.VALIDATION_ERROR,
            "status": 422,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": ErrorCode.INTERNAL_ERROR,
            "status": 500,
        },
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    code = f"HTTP_{exc.status_code}"
    if exc.status_code == 401:
        code = ErrorCode.UNAUTHORIZED
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": code,
            "status": exc.status_code,
        },
    )
# ---------------------------------------------------------------------------
# Routers — add here as domains are implemented
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(directions_router)
app.include_router(fiches_de_poste_router)
app.include_router(recruitment_router)
app.include_router(recruitment_besoins_router)
app.include_router(offres_router)

# ---------------------------------------------------------------------------
# Base routes
# ---------------------------------------------------------------------------
@app.get("/")
def root() -> dict[str, str]:
    return {"message": "RH Flow API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}