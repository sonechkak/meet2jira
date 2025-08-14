import os

from src.services.jira_service import get_jira_service, JiraService


def test_connection_to_jira(jira_client):
    """
    Test the connection to Jira by checking if the client can fetch the current user.
    """
    user = jira_client.current_user()
    assert user is not None, "Failed to connect to Jira or fetch current user."
    assert isinstance(user, str), "Current user should be a string."
    assert len(user) > 0, "Current user should not be an empty string."


def test_jira_client_initialization(jira_client):
    """
    Test the Jira client initialization by checking if the client is an instance of JIRA.
    """
    from jira import JIRA
    assert isinstance(jira_client, JIRA), "Jira client should be an instance of JIRA."
    assert jira_client.server_url == os.getenv("JIRA_API_URL"), "Jira server URL does not match the expected value."

def test_jira_client_authentication(jira_client):
    """
    Test the Jira client authentication by checking if the client can authenticate with the provided credentials.
    """
    assert jira_client._session.auth is not None, "Jira client should have authentication credentials."
    assert jira_client._session.auth[0] == os.getenv("JIRA_API_USER"), "Jira username does not match the expected value."
    assert jira_client._session.auth[1] == os.getenv("JIRA_API_TOKEN"), "Jira API token does not match the expected value."


def test_create_minimal_issue(jira_client):
    """
    Test creating a minimal issue in Jira to ensure the client can create issues.
    """
    jira_service = JiraService(os.getenv("JIRA_API_URL"), os.getenv("JIRA_API_USER"), os.getenv("JIRA_API_TOKEN"))
    try:
        task_key = jira_service.create_minimal_task(
            "Тестовая задача",
            "MEET2JIRA"
        )
        print(f"Задача создана: {task_key}")
    except Exception as e:
        print(f"Ошибка: {e}")
