# meet2jira

Автоматическая система для конвертации записей встреч в задачи Jira с использованием локальной AI модели.

## 🚀 Возможности

- Обработка аудиозаписей встреч и их транскрипция
- Извлечение задач и действий из текста встреч с помощью AI
- Автоматическое создание тикетов в Jira
- Локальная обработка данных (модель от Yandex через Hugging Face)
- RESTful API для интеграции
- Веб-интерфейс для управления

## 🛠 Технологический стек

- **Python 3.11+** - основной язык разработки
- **uv** - современный Python package manager
- **FastAPI** - веб-фреймворк
- **Docker & Docker Compose** - контейнеризация
- **PostgreSQL** - база данных
- **Alembic** - миграции БД
- **Pydantic** - валидация данных
- **Pytest** - тестирование
- **Hugging Face Transformers** - AI модели
- **Whisper** - транскрипция аудио (опционально)

## 📋 Требования

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (для разработки)
- [uv](https://docs.astral.sh/uv/) - современный Python package manager
- Минимум 4GB RAM для AI модели

## ⚡ Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/sonechkak/meet2jira.git
cd meet2jira
```

### 2. Установка uv

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Или через pip
pip install uv
```

### 3. Настройка переменных окружения

```bash
cp .env.example .env
```

Отредактируйте `.env` файл:

```env
# Jira настройки
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ

# База данных
POSTGRES_DB=meet2jira
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
DATABASE_URL=postgresql://postgres:your-password@db:5432/meet2jira

# AI модель
HUGGINGFACE_MODEL=ai-forever/rugpt3large_based_on_gpt2
MODEL_CACHE_DIR=./models

# Приложение
DEBUG=False
SECRET_KEY=your-super-secret-key
```

### 4. Запуск с Docker Compose

```bash
# Сборка и запуск всех сервисов
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f
```

### 5. Инициализация базы данных

```bash
# Применение миграций
docker-compose exec app alembic upgrade head
```

### 6. Проверка работы

Откройте браузер: http://localhost:8000

API документация: http://localhost:8000/docs

## 🔧 Разработка

### Локальная установка с uv

```bash
# Создание и активация виртуального окружения
uv venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows

# Установка зависимостей
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt

# Или используя uv sync (если есть pyproject.toml)
uv sync --dev
```

### Альтернативная установка (legacy)

```bash
# Создание виртуального окружения (устаревший способ)
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Установка зависимостей
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Работа с базой данных

```bash
# Создание новой миграции
alembic revision --autogenerate -m "Description"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

### Загрузка AI модели

```bash
# С uv (рекомендуется)
uv run python scripts/download_model.py

# Или через активированное окружение
python scripts/download_model.py

# Или через Docker
docker-compose exec app python scripts/download_model.py
```

### Запуск тестов

```bash
# С uv (рекомендуется)
uv run pytest

# Тесты с покрытием
uv run pytest --cov=app --cov-report=html

# Только unit тесты
uv run pytest tests/unit/

# Только integration тесты
uv run pytest tests/integration/

# Через активированное окружение (альтернативно)
pytest
pytest --cov=app --cov-report=html
```

### Линтинг и форматирование

```bash
# С uv (рекомендуется)
uv run flake8 app/
uv run black --check app/
uv run isort --check-only app/

# Форматирование
uv run black app/
uv run isort app/

# Через активированное окружение (альтернативно)
flake8 app/
black --check app/
isort --check-only app/
```

## 🤖 Использование AI модели

Проект использует локальную модель от Yandex, доступную через Hugging Face:

### Поддерживаемые модели

- `ai-forever/rugpt3large_based_on_gpt2` (рекомендуется)
- `ai-forever/rugpt3medium_based_on_gpt2`
- `ai-forever/rugpt3small_based_on_gpt2`

### Настройка модели

```python
# app/core/config.py
HUGGINGFACE_MODEL = "ai-forever/rugpt3large_based_on_gpt2"
MODEL_CACHE_DIR = "./models"
MAX_SEQUENCE_LENGTH = 1024
```

## 📖 API

### Основные endpoints

- `POST /file/proccess` - Загрузка и обработка документа с помощью AI
- `GET /file/accept` - Принятие результата и создание задач в Jira
- `POST /file/reject` - Отклонение результата обработки
- `POST /file/reject` - Отклонение результата обработки 
- `POST /file/webhook` - Webhook для внешних сервисов

## 🔧 Конфигурация

### Jira интеграция

1. Создайте API токен в Jira: Account Settings → Security → API tokens
2. Настройте переменные `JIRA_*` в `.env`
3. Убедитесь, что у пользователя есть права на создание задач

## 🚀 Деплой

### Production с Docker

```bash
# Production сборка
docker-compose up -d

# Мониторинг
docker-compose logs -f app
```

### Системные требования

- **CPU**: 2+ ядра
- **RAM**: 6GB+ (4GB для модели + 2GB для приложения)
- **Диск**: 10GB+ свободного места
- **Сеть**: доступ к Jira API

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте feature ветку: `git checkout -b feature/amazing-feature`
3. Внесите изменения и добавьте тесты
4. Проверьте тесты: `pytest`
5. Создайте Pull Request

### Правила коммитов

- Используйте conventional commits: `feat:`, `fix:`, `docs:`, etc.
- Пишите понятные описания изменений
- Добавляйте тесты для новых функций

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. [LICENSE](LICENSE) файл.