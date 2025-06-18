# tasks.py
# Celery задачи для аудиофайлов
from celery import shared_task


@shared_task
def transcribe_audio_task(file_id: int) -> None:
    # TODO: Реализация транскрибации
    pass
