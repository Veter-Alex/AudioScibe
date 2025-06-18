# Fullstack проект

## Структура
- backend/ — серверная часть (FastAPI, Celery, PostgreSQL, Redis, Poetry)
- frontend/ — клиентская часть (React)
- docker-compose.yml — запуск всех сервисов

## Быстрый старт
1. Клонируйте репозиторий
2. Запустите:
   ```bash
   docker-compose up --build
   ```
3. Backend будет доступен на http://localhost:8000, frontend — на http://localhost:3000

## Описание backend
Этот проект использует FastAPI, Celery, PostgreSQL, Redis и Poetry для управления зависимостями и виртуальным окружением.

## Описание frontend
React-приложение для взаимодействия с backend.
