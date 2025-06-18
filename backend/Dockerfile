# Dockerfile for FastAPI backend
FROM python:3.11-slim
WORKDIR /app

# Установить Poetry
RUN pip install --no-cache-dir poetry

# Скопировать pyproject.toml и poetry.lock для установки зависимостей
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Скопировать остальной код
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
