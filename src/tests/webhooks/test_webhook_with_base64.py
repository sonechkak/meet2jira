import requests
import base64
import json


def test_webhook_with_base64():
    """Тест веб-хука с base64 файлом"""

    # Создаем тестовый файл
    test_content = """
    Требования к системе:
    1. Создать API для управления пользователями
    2. Добавить аутентификацию JWT
    3. Реализовать CRUD операции
    4. Написать тесты
    """

    # Кодируем в base64
    encoded_content = base64.b64encode(test_content.encode()).decode()

    webhook_data = {
        "event": "file_upload",
        "webhook_id": "test_12345",
        "project_key": "TEST",
        "epic_key": "TEST-100",
        "file": {
            "name": "requirements.txt",
            "content": encoded_content,
            "mime_type": "text/plain"
        }
    }

    try:
        response = requests.post(
            "http://127.0.0.1:8000/file/webhook",
            json=webhook_data,
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def test_webhook_with_real_file():
    """Тест веб-хука с реальным файлом"""

    # Читаем реальный файл
    file_path = "test_requirements.txt"

    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
            encoded_content = base64.b64encode(file_content).decode()

        webhook_data = {
            "event": "file_upload",
            "webhook_id": f"test_real_{hash(file_path)}",
            "project_key": "REAL",
            "epic_key": None,
            "file": {
                "name": file_path,
                "content": encoded_content,
                "mime_type": "text/plain"
            }
        }

        response = requests.post(
            "http://127.0.0.1:8000/file/webhook",
            json=webhook_data,
            timeout=180
        )

        print(f"Real file test - Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    except FileNotFoundError:
        print(f"File {file_path} not found. Creating test file...")
        create_test_file(file_path)
        test_webhook_with_real_file()
    except Exception as e:
        print(f"Error: {e}")


def create_test_file(filename):
    """Создает тестовый файл с требованиями"""
    content = """
Техническое задание

Цель: Разработать веб-приложение для управления задачами

Функциональные требования:
1. Регистрация и авторизация пользователей
   - Email/пароль
   - JWT токены
   - Роли: admin, user

2. Управление задачами
   - Создание задачи
   - Редактирование задачи
   - Удаление задачи
   - Просмотр списка задач

3. Фильтрация и поиск
   - По статусу (новая, в работе, завершена)
   - По дате создания
   - По исполнителю

Технические требования:
- Backend: FastAPI + PostgreSQL
- Frontend: React
- API документация: Swagger
- Тестирование: pytest
- Контейнеризация: Docker

Дополнительно:
- Логирование всех действий
- Email уведомления
- Backup базы данных
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Test file {filename} created")


def test_webhook_error_cases():
    """Тест обработки ошибок"""

    test_cases = [
        # Без события
        {
            "webhook_id": "error_test_1",
            "file": {"name": "test.txt", "content": "dGVzdA=="}
        },
        # Без файла
        {
            "event": "file_upload",
            "webhook_id": "error_test_2"
        },
        # Неправильный base64
        {
            "event": "file_upload",
            "webhook_id": "error_test_3",
            "file": {"name": "test.txt", "content": "invalid_base64!!!"}
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Error Test Case {i} ---")
        try:
            response = requests.post(
                "http://127.0.0.1:8000/file/webhook",
                json=test_case,
                timeout=60
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Exception: {e}")


if __name__ == "__main__":
    print("=== Testing Webhook ===")

    print("\n1. Testing with base64 content:")
    test_webhook_with_base64()

    print("\n2. Testing with real file:")
    test_webhook_with_real_file()

    print("\n3. Testing error cases:")
    test_webhook_error_cases()
