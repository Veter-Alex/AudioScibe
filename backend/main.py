from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from audio_files.routes import router as audio_files_router
from core.config import settings
from core.exceptions import AppException
from core.logger import logger

app = FastAPI()


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Кастомный обработчик ошибок приложения.
    """
    logger.error(
        (
            f"{request.method} {request.url.path} - {exc.error_code}: {exc.detail} "
            f"| meta={exc.meta}"
        )
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "detail": exc.detail,
            "meta": exc.meta,
        },
    )


@app.get("/")
def read_root():
    logger.info("Root endpoint was called")
    return {"message": "Hello from FastAPI!"}


@app.get("/settings", response_model=dict)
def get_app_settings() -> dict:
    """
    Возвращает все текущие настройки приложения (без чувствительных данных).
    """
    # Преобразуем настройки в dict и фильтруем чувствительные поля
    exclude_keys = {
        "JWT_SECRET",
        "FIRST_ADMIN_PASSWORD",
        "DB_PASSWORD",
        "REDIS_PASSWORD",
    }
    settings_dict = {
        k: v for k, v in settings.model_dump().items() if k not in exclude_keys
    }
    return settings_dict


app.include_router(audio_files_router, prefix="/audio_files", tags=["audio_files"])
