# routes.py
# API-эндпоинты для аудиофайлов
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from audio_files import services
from audio_files.schemas import AudioFileRead, AudioFileUploadRequest
from core.config import WhisperModel
from core.database import get_async_session

router = APIRouter()


@router.post(
    "/upload",
    response_model=AudioFileRead,
    summary="Загрузить аудиофайл",
    description=(
        "Загрузка нового аудиофайла. Укажите модель и путь внутри папки модели. "
        "Возвращает id и имя файла."
    ),
)
async def upload_audio(
    model_name: WhisperModel = Query(
        ...,
        description=(
            "Название модели Whisper для транскрибирования " "(выберите из списка)"
        ),
    ),
    relative_path: str = Depends(AudioFileUploadRequest),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
):
    audio = await services.save_audio_file(
        file, model_name.value, relative_path.relative_path, session
    )
    print(f"[DEBUG] Uploaded audio file: {audio.filename}, path: {audio.file_path}")
    print(f"[DEBUG] Audio file ID: {audio.id}")
    return AudioFileRead.model_validate(audio)


@router.get(
    "/",
    response_model=List[AudioFileRead],
    summary="Список аудиофайлов",
    description="Получить список всех загруженных аудиофайлов.",
)
async def list_audio_files(session: AsyncSession = Depends(get_async_session)):
    audios = await services.list_audio_files(session)
    return [AudioFileRead.model_validate(a) for a in audios]


@router.delete(
    "/dir",
    summary="Удалить директорию с аудиофайлами",
    description=(
        "ВНИМАНИЕ!!!"
        "Удаляет директорию (и все вложенные файлы) внутри "
        "uploads/<model>/<relative_path>."
    ),
)
async def delete_audio_directory(
    model_name: WhisperModel = Query(..., description="Название модели Whisper"),
    relative_path: str = Query(
        "", description="Относительный путь внутри модели (может быть пустым)"
    ),
):
    result = await services.delete_directory(model_name.value, relative_path)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["detail"])
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["detail"])
    return result


@router.get(
    "/{file_id}",
    response_model=AudioFileRead,
    summary="Информация об аудиофайле",
    description="Получить подробную информацию об аудиофайле по его id.",
)
async def get_audio_file(
    file_id: int, session: AsyncSession = Depends(get_async_session)
):
    audio = await services.get_audio_file(file_id, session)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")
    return AudioFileRead.model_validate(audio)


@router.get(
    "/{file_id}/download",
    summary="Скачать аудиофайл",
    description="Скачать оригинальный аудиофайл по его id.",
)
async def download_audio_file(
    file_id: int, session: AsyncSession = Depends(get_async_session)
):
    audio = await services.get_audio_file(file_id, session)
    if not audio or not audio.file_path:
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(audio.file_path, filename=audio.filename)


@router.delete(
    "/{file_id}",
    summary="Удалить аудиофайл",
    description="Удалить аудиофайл по его id.",
)
async def delete_audio_file(
    file_id: int, session: AsyncSession = Depends(get_async_session)
):
    deleted = await services.delete_audio_file(file_id, session)
    if not deleted:
        raise HTTPException(status_code=404, detail="Audio file not found")
    return {"status": "deleted", "id": file_id}
