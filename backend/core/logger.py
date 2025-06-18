# backend/app/core/logger.py
import os
import sys

from loguru import logger

# Создаем директорию для логов, если её нет
os.makedirs("logs", exist_ok=True)

# Очищаем стандартные обработчики (если есть)
logger.remove()

# Добавляем обработчик для вывода в консоль с уровнем DEBUG
logger.add(
    sys.stdout,
    level="DEBUG",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - {message}"
    ),
    colorize=True,
)

# Добавляем обработчик для записи логов уровня INFO в файл app.log
logger.add(
    "logs/app.log",
    level="INFO",
    filter=lambda record: record["level"].no >= 20,
    rotation="10 MB",  # Перезапись логов при достижении 10 МБ
    retention="30 days",  # Хранение логов 30 дней
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | {level} | " "{name}:{function}:{line} - {message}"
    ),
    enqueue=True,  # Безопасная асинхронная запись
)

# Добавляем обработчик для записи логов уровня DEBUG в файл debug.log
logger.add(
    "logs/debug.log",
    level="DEBUG",
    rotation="5 MB",
    retention="30 days",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | {level} | " "{name}:{function}:{line} - {message}"
    ),
    enqueue=True,
)

# Добавляем обработчик для записи ошибок уровня ERROR в отдельный файл
logger.add(
    "logs/errors.log",
    level="ERROR",
    filter=lambda record: record["level"].no >= 40,
    rotation="5 MB",
    retention="30 days",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | {level} | " "{name}:{function}:{line} - {message}"
    ),
    enqueue=True,
)

# Пример использования:
# logger.debug("Это debug сообщение")
# logger.info("Это info сообщение")
# logger.warning("Это warning сообщение")
# logger.error("Это error сообщение")
# logger.critical("Это critical сообщение")
