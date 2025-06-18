import os
import shutil
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from audio_files.models import AudioFile

UPLOAD_DIR = "./uploads"


def _normalize_relative_path(relative_path: str) -> str:
    print(f"[DEBUG] _normalize_relative_path input: {relative_path}")
    path = relative_path.replace("\\", "/").strip().strip("/")
    if not path:
        result = ""
    elif "." in os.path.basename(path):
        # Если basename похож на файл — возвращаем только папки
        result = os.path.dirname(path)
    else:
        # Весь путь — это папки
        result = path
    print(f"[DEBUG] _normalize_relative_path output: {result}")
    return result


async def save_audio_file(
    file: UploadFile,
    model_name: str,
    relative_path: str,
    session: AsyncSession,
) -> AudioFile:
    print(f"[DEBUG] save_audio_file relative_path: {relative_path}")
    # Гарантируем, что корневая папка для загрузок существует (создаётся один раз)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    # Нормализуем относительный путь (оставляем только папку, даже если пользователь
    # указал файл)
    rel_dir = _normalize_relative_path(relative_path)
    print(f"[DEBUG] save_audio_file rel_dir: {rel_dir}")
    if rel_dir:
        # Путь в базе и на диске: uploads/<model>/<relative_path>/<имя_файла>
        db_file_path = os.path.join(model_name, rel_dir, file.filename)
        target_dir = os.path.join(UPLOAD_DIR, model_name, rel_dir)
    else:
        # Если относительный путь не указан — кладём в корень папки модели
        db_file_path = os.path.join(model_name, file.filename)
        target_dir = os.path.join(UPLOAD_DIR, model_name)
    # Создаём целевую директорию для файла (включая все вложенные папки)
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, file.filename)
    # Сохраняем файл на диск
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    # Создаём запись в базе данных
    audio = AudioFile(
        filename=file.filename, file_path=db_file_path, whisper_model=model_name
    )
    session.add(audio)
    await session.commit()
    await session.refresh(audio)
    return audio


async def get_audio_file(file_id: int, session: AsyncSession) -> Optional[AudioFile]:
    result = await session.execute(select(AudioFile).where(AudioFile.id == file_id))
    audio = result.scalar_one_or_none()
    return audio


async def list_audio_files(session: AsyncSession) -> List[AudioFile]:
    result = await session.execute(select(AudioFile))
    return result.scalars().all()


async def delete_audio_file(file_id: int, session: AsyncSession) -> bool:
    audio = await get_audio_file(file_id, session)
    if not audio:
        return False
    # Удаляем файл с диска (используем абсолютный путь)
    file_path = os.path.join(UPLOAD_DIR, audio.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    await session.delete(audio)
    await session.commit()
    return True


async def delete_directory(model_name: str, relative_path: str) -> dict:
    """
    Удаляет директорию (и все вложенные файлы) внутри
    uploads/<model_name>/<relative_path>.
    Возвращает информацию о результате.
    """
    rel_dir = _normalize_relative_path(relative_path)
    # Формируем абсолютный путь
    target_dir = (
        os.path.join(UPLOAD_DIR, model_name, rel_dir)
        if rel_dir
        else os.path.join(UPLOAD_DIR, model_name)
    )
    # Проверка безопасности: путь должен быть внутри UPLOAD_DIR
    abs_upload_dir = os.path.abspath(UPLOAD_DIR)
    abs_target_dir = os.path.abspath(target_dir)
    if not abs_target_dir.startswith(abs_upload_dir):
        return {"status": "error", "detail": "Недопустимый путь для удаления"}
    if not os.path.exists(abs_target_dir):
        return {"status": "not_found", "detail": "Директория не существует"}
    try:
        shutil.rmtree(abs_target_dir)
        return {"status": "deleted", "path": abs_target_dir}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
