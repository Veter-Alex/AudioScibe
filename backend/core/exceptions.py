# backend/app/core/exceptions.py
from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Базовое исключение приложения с дополнительными метаданными."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.meta = meta or {}


# =============================
# АУТЕНТИФИКАЦИЯ И АВТОРИЗАЦИЯ
# =============================
class AuthenticationException(AppException):
    """Ошибка аутентификации"""

    def __init__(self, detail: str = "Неверные учетные данные"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTH_ERROR",
        )


class PermissionDeniedException(AppException):
    """Ошибка доступа (недостаточно прав)"""

    def __init__(self, detail: str = "Доступ запрещен"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_DENIED",
        )


# =============================
# РАБОТА С ДАННЫМИ
# =============================
class DataValidationException(AppException):
    """Ошибка валидации данных"""

    def __init__(self, detail: str, errors: Optional[Dict] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
            meta={"errors": errors} if errors else None,
        )


class DatabaseException(AppException):
    """Ошибка работы с базой данных"""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при выполнении операции: {operation}",
            error_code="DATABASE_ERROR",
            meta={"reason": reason},
        )


class NotFoundException(AppException):
    """Запрошенный ресурс не найден"""

    def __init__(self, resource_type: str, resource_id: Optional[Any] = None):
        detail = f"{resource_type} не найден"
        if resource_id is not None:
            detail = f"{resource_type} с ID {resource_id} не найден"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
            meta={"resource_type": resource_type, "resource_id": resource_id},
        )


class ConflictException(AppException):
    """Конфликт данных (уже существует)"""

    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource_type} '{identifier}' уже существует",
            error_code="CONFLICT",
            meta={"resource_type": resource_type, "identifier": identifier},
        )


# =============================
# БИЗНЕС-ЛОГИКА
# =============================
class ProcessingException(AppException):
    """Ошибка обработки данных"""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки: {operation}",
            error_code="PROCESSING_ERROR",
            meta={"reason": reason},
        )


class ExternalServiceException(AppException):
    """Ошибка внешнего сервиса"""

    def __init__(self, service_name: str, reason: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ошибка сервиса {service_name}",
            error_code="EXTERNAL_SERVICE_ERROR",
            meta={"reason": reason, "service": service_name},
        )


# =============================
# ФАЙЛОВЫЕ ОПЕРАЦИИ
# =============================
class FileOperationException(AppException):
    """Ошибка работы с файлами"""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка файловой операции: {operation}",
            error_code="FILE_ERROR",
            meta={"reason": reason},
        )


class InvalidFileException(AppException):
    """Некорректный файл"""

    def __init__(self, detail: str, allowed_formats: Optional[list] = None):
        meta = {"allowed_formats": allowed_formats} if allowed_formats else None
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="INVALID_FILE",
            meta=meta,
        )


class ConfigurationException(AppException):
    """Ошибка конфигурации приложения"""

    def __init__(self, key: str, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка конфигурации приложения: {key}",
            error_code="CONFIGURATION_ERROR",
            meta={"key": key, "message": message},
        )
