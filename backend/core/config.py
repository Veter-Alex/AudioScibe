# backend/app/core/config.py
from enum import Enum
from functools import lru_cache
from typing import Any, Optional
from urllib.parse import quote_plus

from pydantic import EmailStr, Field, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings

# Импорт кастомных исключений
from core.exceptions import ConfigurationException

# Импорт логгера
from core.logger import logger


# =============================
# ПЕРЕЧИСЛЕНИЯ И ТИПЫ
# =============================
class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class StatusProcessing(str, Enum):
    PENDING = "pending"  # ожидает обработки
    PROCESSING = "processing"  # в процессе обработки
    DONE = "done"  # обработка завершена
    ERROR = "error"  # ошибка


class WhisperModel(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V2 = "large_v2"
    LARGE_V3 = "large_v3"


class ModelType(str, Enum):
    """
    Перечисление типов ИИ-моделей, поддерживаемых системой.

    Значения:
        TRANSCRIPT: Модель транскрибации (преобразование аудио в текст)
        TRANSLATE: Модель машинного перевода (текст между языками)
        SUMMARY: Модель суммаризации текста (создание сокращённых версий)
    """

    TRANSCRIPT = "transcript"  # Константа для моделей распознавания речи
    TRANSLATE = "translate"  # Константа для переводческих моделей
    SUMMARY = "summary"  # Константа для моделей сжатия текста


# =============================
# КОНСТАНТЫ И ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ
# =============================
DEFAULT_APP_NAME = "AudioScribe"
DEFAULT_VERSION = "1.0.0"
DEFAULT_DEBUG = False
DEFAULT_ENVIRONMENT: Environment = Environment.DEVELOPMENT
DEFAULT_DB_PORT = "5432"
DEFAULT_DB_POOL_SIZE = 20
DEFAULT_DB_MAX_OVERFLOW = 10
DEFAULT_DB_POOL_RECYCLE = 3600  # секунд (1 час)
DEFAULT_DB_USE_SSL = True
DEFAULT_WHISPER_MODEL: WhisperModel = WhisperModel.BASE
DEFAULT_PROCESSING_STATUS: StatusProcessing = StatusProcessing.PENDING
DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_JWT_EXPIRE_MINUTES = 30
DEFAULT_FIRST_ADMIN_USERNAME = "admin"
DEFAULT_FIRST_ADMIN_PASSWORD = (
    "adminadmin"  # Пароль должен быть изменён при первом входе
)
DEFAULT_FIRST_ADMIN_EMAIL = "admin@example.com"
DEFAULT_REDIS_HOST = "redis"
DEFAULT_REDIS_PORT = 6379


# =============================
# КЛАСС НАСТРОЕК ПРИЛОЖЕНИЯ
# =============================
class Settings(BaseSettings):
    """
    Центральный класс для управления настройками приложения.
    Настройки загружаются в следующем порядке приоритета:
    1. Переменные окружения
    2. .env файл
    3. Значения по умолчанию, указанные в классе
    """

    # Основные настройки приложения
    APP_NAME: str = Field(DEFAULT_APP_NAME, description="Название приложения")
    VERSION: str = Field(DEFAULT_VERSION, description="Версия приложения")
    DEBUG: bool = Field(DEFAULT_DEBUG, description="Режим отладки")
    ENVIRONMENT: Environment = Field(
        default=DEFAULT_ENVIRONMENT,
        description="Среда выполнения: development, production или testing",
    )

    # Настройки подключения к базе данных
    DB_USER: Optional[str] = Field(
        None, min_length=1, description="Имя пользователя базы данных"
    )
    DB_PASSWORD: Optional[str] = Field(
        None, min_length=1, description="Пароль пользователя базы данных"
    )
    DB_HOST: Optional[str] = Field(None, min_length=1, description="Хост базы данных")
    DB_PORT: str = Field(DEFAULT_DB_PORT, description="Порт базы данных")
    DB_NAME: Optional[str] = Field(None, min_length=1, description="Имя базы данных")
    SQLALCHEMY_DATABASE_URL: Optional[PostgresDsn] = Field(
        None, description="Полный URL для подключения к базе данных"
    )

    # Настройки пула соединений
    DB_POOL_SIZE: int = Field(
        default=DEFAULT_DB_POOL_SIZE,
        gt=0,
        description="Количество постоянных соединений в пуле",
    )
    DB_MAX_OVERFLOW: int = Field(
        default=DEFAULT_DB_MAX_OVERFLOW,
        ge=0,
        description="Максимальное количество временных соединений",
    )
    DB_POOL_RECYCLE: int = Field(
        default=DEFAULT_DB_POOL_RECYCLE,
        gt=0,
        description="Время жизни соединения в секундах до пересоздания",
    )
    DB_USE_SSL: bool = Field(
        DEFAULT_DB_USE_SSL,
        description="Использовать SSL-шифрование для подключения к БД",
    )

    # Настройки обработки аудио
    # Директория для хранения аудиофайлов (используется внутри контейнера)
    UPLOAD_DIR: str = Field(
        default="/app/uploads", description="Директория для хранения аудиофайлов"
    )
    WHISPER_DEFAULT_MODEL: WhisperModel = Field(
        default=DEFAULT_WHISPER_MODEL,
        description="Модель Whisper по умолчанию для обработки аудио",
    )

    # Настройки безопасности
    JWT_SECRET: str = Field(
        ...,
        min_length=32,
        description="Секретный ключ для подписи JWT токенов",
    )
    JWT_ALGORITHM: str = Field(
        default=DEFAULT_JWT_ALGORITHM, description="Алгоритм подписи JWT токенов"
    )
    JWT_EXPIRE_MINUTES: int = Field(
        default=DEFAULT_JWT_EXPIRE_MINUTES,
        gt=0,
        description="Время жизни access токена в минутах",
    )

    FIRST_ADMIN_USERNAME: str = Field(
        default=DEFAULT_FIRST_ADMIN_USERNAME,
        description="Имя пользователя первого администратора",
    )

    FIRST_ADMIN_PASSWORD: str = Field(
        default=DEFAULT_FIRST_ADMIN_PASSWORD,
        min_length=8,
        description="Пароль первого администратора (обязательный)",
    )

    FIRST_ADMIN_EMAIL: EmailStr = Field(
        default=DEFAULT_FIRST_ADMIN_EMAIL, description="Email первого администратора"
    )

    FIRST_ADMIN_ENABLED: bool = Field(
        default=False, description="Разрешить создание первого администратора через API"
    )

    # Настройки Redis
    REDIS_HOST: str = Field(default=DEFAULT_REDIS_HOST, description="Хост Redis")
    REDIS_PORT: int = Field(default=DEFAULT_REDIS_PORT, description="Порт Redis")
    USE_REDIS_QUEUE: bool = Field(
        default=True, description="Использовать Redis для очередей задач"
    )

    # ======================
    # ВАЛИДАТОРЫ
    # ======================
    # Валидатор для пароля
    @field_validator("FIRST_ADMIN_PASSWORD")
    def validate_admin_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов")
        return v

    @model_validator(mode="after")
    def assemble_db_connection(self) -> "Settings":
        """Автоматически собирает DSN для подключения к БД, если он не задан явно."""
        if self.SQLALCHEMY_DATABASE_URL:
            logger.debug(
                "Базовый URL БД уже задан", db_url=str(self.SQLALCHEMY_DATABASE_URL)
            )
            return self

        required_fields = {
            "DB_USER": self.DB_USER,
            "DB_PASSWORD": self.DB_PASSWORD,
            "DB_HOST": self.DB_HOST,
            "DB_NAME": self.DB_NAME,
        }
        missing = [name for name, value in required_fields.items() if value is None]
        if missing:
            logger.error("Отсутствуют обязательные параметры БД", missing=missing)
            raise ConfigurationException(
                key="database_connection",
                message=f"Отсутствуют обязательные параметры БД: {', '.join(missing)}",
            )

        try:
            password = quote_plus(self.DB_PASSWORD)  # type: ignore[arg-type]
            dsn_str = (
                f"postgresql+asyncpg://"
                f"{self.DB_USER}:{password}@"
                f"{self.DB_HOST}:{self.DB_PORT}/"
                f"{self.DB_NAME}"
            )
            logger.info("Сформирован DSN для БД", dsn=dsn_str)
            self.SQLALCHEMY_DATABASE_URL = PostgresDsn(dsn_str)
        except Exception as e:
            logger.exception("Ошибка формирования DSN для БД", exc_info=True)
            raise ConfigurationException(
                key="database_connection",
                message=f"Ошибка формирования DSN: {str(e)}",
            )

        return self

    @field_validator("ENVIRONMENT", mode="before")
    def validate_environment(cls, value: Any) -> str:
        """Нормализует значение среды выполнения."""
        logger.debug("Валидация окружения", raw_value=value)
        if isinstance(value, str):
            normalized = value.lower()
        elif isinstance(value, Environment):
            normalized = value.value
        else:
            normalized = str(value).lower()
        logger.info("Окружение нормализовано", environment=normalized)
        return normalized

    @field_validator("WHISPER_DEFAULT_MODEL", mode="before")
    def validate_whisper_model(cls, value: Any) -> WhisperModel:
        """Проверяет и нормализует модель Whisper."""
        logger.debug("Валидация модели Whisper", raw_value=value)
        if isinstance(value, WhisperModel):
            logger.info("Модель Whisper уже валидна", model=value)
            return value
        if isinstance(value, str):
            try:
                model = WhisperModel(value)
                logger.info("Модель Whisper успешно определена", model=model)
                return model
            except ValueError:
                valid_models = ", ".join([m.value for m in WhisperModel])
                logger.error("Недопустимая модель Whisper", invalid_model=value)
                raise ConfigurationException(
                    key="whisper_model",
                    message=(
                        f"Недопустимая модель Whisper: '{value}'. "
                        f"Допустимые значения: {valid_models}"
                    ),
                )
        logger.error("Неподдерживаемый тип модели Whisper", type=type(value))
        raise ConfigurationException(
            key="whisper_model",
            message=(
                f"Неподдерживаемый тип для модели Whisper: {type(value)}. "
                "Ожидается строка или значение перечисления WhisperModel."
            ),
        )

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# =============================
# ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ НАСТРОЕК
# =============================
@lru_cache
def get_settings() -> Settings:
    """Возвращает экземпляр настроек приложения с кэшированием."""
    try:
        logger.info("Инициализация настроек приложения")
        settings = Settings()  # type: ignore[call-arg]
        logger.info(
            "Настройки успешно загружены",
            app_name=settings.APP_NAME,
            environment=settings.ENVIRONMENT,
        )
        return settings
    except ConfigurationException as e:
        logger.critical("Ошибка конфигурации приложения", error=str(e), exc_info=True)
        raise e
    except Exception as e:
        logger.exception("Непредвиденная ошибка при загрузке настроек", exc_info=True)
        raise ConfigurationException(
            key="settings_initialization",
            message=f"Непредвиденная ошибка при загрузке настроек: {str(e)}",
        )


# Глобальный экземпляр настроек для импорта
settings = get_settings()
