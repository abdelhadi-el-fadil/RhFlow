import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger

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
async def log_requests(request: Request, call_next):
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
# Exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# ---------------------------------------------------------------------------
# Routers — add here as domains are implemented
# ---------------------------------------------------------------------------
from app.routers.auth import router as auth_router
app.include_router(auth_router)

# ---------------------------------------------------------------------------
# Base routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "RH Flow API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}