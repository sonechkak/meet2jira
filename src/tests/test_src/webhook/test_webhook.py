import base64
import json

import requests


def test_webhook_with_jira_creation():
    """Тест веб-хука с созданием задач в Jira"""

    test_content = """
    Требования для новой системы:

    1. Создать API для пользователей
    2. Добавить аутентификацию через JWT
    3. Реализовать CRUD операции для товаров
    4. Создать админ панель
    5. Написать документацию API
    """

    encoded_content = base64.b64encode(test_content.encode()).decode()

    webhook_data = {
        "event": "file_upload",
        "webhook_id": "jira_test_123",
        "project_key": "MEET2JIRA",
        "epic_key": "TEST-1",
        "file": {
            "name": "requirements_for_jira.txt",
            "content": encoded_content,
            "mime_type": "text/plain",
        },
    }

    print("Testing webhook with Jira task creation...")
    print(f"Project: {webhook_data['project_key']}")
    print(f"Epic: {webhook_data.get('epic_key', 'None')}")

    try:
        response = requests.post(
            "http://127.0.0.1:8000/file/webhook", json=webhook_data
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")

            # Проверяем результат Jira
            if "jira_result" in result:
                jira_info = result["jira_result"]
                print(f"\n🎯 Jira Tasks Created: {jira_info.get('tasks_count', 0)}")
                print(f"Project: {jira_info.get('project_key')}")

                if "created_tasks" in jira_info:
                    print("Created tasks:")
                    for task in jira_info["created_tasks"]:
                        print(f"  - {task}")
            else:
                print("\n❌ No Jira tasks were created")
                print("Debug info:", json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error: {response.text}")

    except requests.exceptions.Timeout:
        print("⏰ Request timed out (this might happen with large processing)")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_webhook_with_jira_creation()
