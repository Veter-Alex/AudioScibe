import os
import shutil
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from audio_files.models import AudioFile
from core.logger import logger

UPLOAD_DIR = "./uploads"


def _normalize_relative_path(relative_path: str) -> str:
    path = relative_path.replace("\\", "/").strip().strip("/")
    if not path:
        result = ""
    elif "." in os.path.basename(path):
        # Если basename похож на файл — возвращаем только папки
        result = os.path.dirname(path)
    else:
        # Весь путь — это папки
        result = path
    return result


async def save_audio_file(
    file: UploadFile,
    model_name: str,
    relative_path: str,
    session: AsyncSession,
) -> AudioFile:
    try:
        logger.info(
            f"Загрузка файла: {file.filename}, модель: {model_name}, "
            f"относительный путь: {relative_path}"
        )
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        # Нормализуем относительный путь (оставляем только папку, даже если пользователь
        # указал файл)
        rel_dir = _normalize_relative_path(relative_path) or ""
        if rel_dir:
            db_file_path = os.path.join(model_name, rel_dir, file.filename)
            target_dir = os.path.join(UPLOAD_DIR, model_name, rel_dir)
        else:
            db_file_path = os.path.join(model_name, file.filename)
            target_dir = os.path.join(UPLOAD_DIR, model_name)
        # Создаём целевую директорию для файла (включая все вложенные папки)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, file.filename)
        # Сохраняем файл на диск
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"Файл сохранён на диск: {file_path}")
        # Создаём запись в базе данных
        audio = AudioFile(
            filename=file.filename, file_path=db_file_path, whisper_model=model_name
        )
        session.add(audio)
        await session.commit()
        await session.refresh(audio)
        logger.info(f"Запись о файле добавлена в БД: {db_file_path}")
        return audio
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла: {file.filename}, ошибка: {e}")
        raise


async def get_audio_file(file_id: int, session: AsyncSession) -> Optional[AudioFile]:
    result = await session.execute(select(AudioFile).where(AudioFile.id == file_id))
    audio = result.scalar_one_or_none()
    return audio


async def list_audio_files(session: AsyncSession) -> list[AudioFile]:
    result = await session.execute(select(AudioFile))
    return list(result.scalars().all())


async def delete_audio_file(file_id: int, session: AsyncSession) -> bool:
    audio = await get_audio_file(file_id, session)
    if not audio:
        logger.warning(f"Попытка удалить несуществующий файл с id={file_id}")
        return False
    file_path = os.path.join(UPLOAD_DIR, str(audio.file_path))
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Файл удалён с диска: {file_path}")
        else:
            logger.warning(f"Файл для удаления не найден на диске: {file_path}")
    except Exception as e:
        logger.error(f"Ошибка при удалении файла с диска: {file_path}, ошибка: {e}")
    await session.delete(audio)
    await session.commit()
    logger.info(f"Запись о файле с id={file_id} удалена из БД")
    return True


async def delete_directory(model_name: str, relative_path: str) -> dict:
    """
    Удаляет директорию (и все вложенные файлы) внутри
    uploads/<model_name>/<relative_path>.
    Возвращает информацию о результате.
    """
    rel_dir = _normalize_relative_path(relative_path) or ""
    target_dir = (
        os.path.join(UPLOAD_DIR, model_name, rel_dir)
        if rel_dir
        else os.path.join(UPLOAD_DIR, model_name)
    )
    abs_upload_dir = os.path.abspath(UPLOAD_DIR)
    abs_target_dir = os.path.abspath(target_dir)
    if not abs_target_dir.startswith(abs_upload_dir):
        logger.error(
            f"Попытка удалить директорию вне разрешённой области: {abs_target_dir}"
        )
        return {"status": "error", "detail": "Недопустимый путь для удаления"}
    if not os.path.exists(abs_target_dir):
        logger.warning(f"Директория для удаления не найдена: {abs_target_dir}")
        return {"status": "not_found", "detail": "Директория не существует"}
    try:
        shutil.rmtree(abs_target_dir)
        logger.info(f"Директория удалена: {abs_target_dir}")
        return {"status": "deleted", "path": abs_target_dir}
    except Exception as e:
        logger.error(f"Ошибка при удалении директории: {abs_target_dir}, ошибка: {e}")
        return {"status": "error", "detail": str(e)}
