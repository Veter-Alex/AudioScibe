"""
Модуль описания ORM-модели для хранения информации об аудиофайлах в базе данных.

Содержит:
- Класс AudioFile: модель SQLAlchemy для таблицы audio_files
- Описание всех ключевых полей аудиофайла
- Возможность расширения дополнительными полями (язык, ошибки, пользователь и т.д.)
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer, String, Text

from core.config import StatusProcessing, WhisperModel
from core.database import Base


class AudioFile(Base):
    """
    ORM-модель AudioFile для хранения информации об аудиофайлах.
    Таблица: audio_files
    """

    __tablename__ = "audio_files"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный идентификатор аудиофайла (автоинкремент)",
    )

    filename = Column(
        String(255),
        nullable=False,
        comment="Оригинальное имя файла при загрузке (без пути)",
    )

    file_path = Column(
        String(500),
        nullable=False,
        comment="Путь к файлу относительно папки загрузки (UPLOAD_DIR)",
    )

    file_language = Column(
        String(10),
        nullable=True,
        comment="Язык аудиофайла в формате ISO 639-1 (например, 'ru', 'en')",
    )

    upload_time = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="Дата и время загрузки файла пользователем (UTC)",
    )

    start_processing_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата и время начала обработки файла (UTC)",
    )

    finished_processing_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата и время завершения обработки файла (UTC)",
    )

    status_processing = Column(
        SqlEnum(StatusProcessing, name="status_processing_enum"),
        default=StatusProcessing.PENDING,
        nullable=False,
        comment="Текущий статус обработки файла (pending, processing, done, error)",
    )

    error_processing = Column(
        String(255),
        nullable=True,
        comment="Описание ошибки обработки файла, если возникла",
    )

    transcript = Column(
        Text,
        nullable=True,
        comment="Результат транскрибации аудиофайла (если уже обработан)",
    )

    whisper_model = Column(
        SqlEnum(WhisperModel, name="whisper_model_enum"),
        nullable=False,
        comment="Модель Whisper для транскрибирования",
    )

    def __repr__(self) -> str:
        """
        Строковое представление объекта AudioFile для отладки и логирования.
        """
        return f"<AudioFile(id={self.id}, filename={self.filename})>"
