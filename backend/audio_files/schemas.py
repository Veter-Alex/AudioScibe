"""
Pydantic-схемы для работы с аудиофайлами (audio_file).

Используются для:
- Валидации входных и выходных данных API
- Описания структуры данных аудиофайла
- Безопасной передачи данных между слоями приложения
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from core.config import StatusProcessing


class AudioFileBase(BaseModel):
    """
    Базовая схема аудиофайла (общие поля для чтения и записи).
    """

    filename: str = Field(
        ...,
        max_length=255,
        description="Оригинальное имя файла при загрузке (без пути)",
    )
    file_language: Optional[str] = Field(
        None,
        max_length=10,
        description="Язык аудиофайла в формате ISO 639-1 (например, 'ru', 'en')",
    )
    transcript: Optional[str] = Field(
        None, description="Результат транскрибации аудиофайла (если уже обработан)"
    )
    whisper_model: str = Field(..., description="Модель Whisper для транскрибирования")


class AudioFileCreate(AudioFileBase):
    """
    Схема для создания аудиофайла (POST /audio/upload).
    """


class AudioFileRead(AudioFileBase):
    """
    Схема для чтения аудиофайла (ответ API).
    """

    id: int
    file_path: str = Field(
        ..., description="Путь к файлу относительно папки загрузки (UPLOAD_DIR)"
    )
    upload_time: Optional[datetime] = Field(
        None, description="Дата и времени загрузки файла пользователем (UTC)"
    )
    start_processing_at: Optional[datetime] = Field(
        None, description="Дата и время начала обработки файла (UTC)"
    )
    finished_processing_at: Optional[datetime] = Field(
        None, description="Дата и время завершения обработки файла (UTC)"
    )
    status_processing: StatusProcessing = Field(
        ...,
        description=(
            "Текущий статус обработки файла (pending, processing, done, error)"
        ),
    )
    error_processing: Optional[str] = Field(
        None, description="Описание ошибки обработки файла, если возникла"
    )

    class Config:
        from_attributes = True


class AudioFileUploadRequest(BaseModel):
    relative_path: str = Field(
        "",
        description=(
            "Путь внутри папки модели. Только прямой слэш ('/') как разделитель. "
            "Не должен начинаться с '/' или содержать '..' или ''."
        ),
    )

    @field_validator("relative_path")
    def validate_path(cls, v):
        if "\\" in v:
            raise ValueError(
                "Используйте только прямой слэш '/' для разделения директорий"
            )
        if v.startswith("/"):
            raise ValueError(
                "Путь не должен начинаться с '/' (абсолютный путь запрещён)"
            )
        if ".." in v:
            raise ValueError("Путь не должен содержать '..'")
        if re.search(r'[<>:"|?*]', v):
            raise ValueError("Путь содержит недопустимые символы")
        return v
