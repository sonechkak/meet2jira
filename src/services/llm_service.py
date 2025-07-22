import requests
import logging
from typing import Dict

from src.pipeline.elements.base import Element


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LlmService(Element):
    """Сервис для ламы."""

    def __init__(
            self,
            prompt: str,
            model="yandex-gpt",
            base_url="http://localhost:11434") -> None:
        """Инициализация сервиса LLM."""
        logger.info("Инициализация LLM сервиса с моделью %s и базовым URL %s", model, base_url)
        super().__init__(model=model, tools=[], prompt="", obj=None)
        self.prompt = prompt
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"

    def run(self) -> Dict[str, str]:
        """Вызов API model для получения ответа на запрос."""
        try:
            logger.info(f"Вызов модели {self.model}")

            payload = {
                "model": self.model,
                "prompt": self.prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 2048,
                }
            }

            logger.info(f"Отправка запроса к модели: {self.api_url}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers={
                    "Content-Type": "application/json"
                },
                timeout=120
            )

            logger.info("Запрос отправлен, ожидаем ответа...")
            response.raise_for_status()  # Проверка на ошибки HTTP
            logger.info("Ответ получен успешно.")

            response_data = response.json()
            logger.info("Обработка ответа от модели...")
            generated_text = response_data.get("response", "")

            if generated_text and generated_text.strip():
                cleaned_text = generated_text.strip()
                logger.info(f"Получен ответ длиной {len(cleaned_text)} символов.")
                return {
                    "generated_response": cleaned_text,
                }
            else:
                logger.warning("Модель вернула пустой ответ")
                return {
                    "error": "Модель вернула пустой ответ",
                    "response": ""
                }

        except Exception as e:
            logger.error(f"Ошибка при вызове API model: {str(e)}")
            return {
                "error": f"Ошибка при вызове API model: {str(e)}",
                "response": ""
            }

        except requests.exceptions.Timeout:
            error_msg = "Превышено время ожидания ответа от модели"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "response": ""
            }

        except requests.exceptions.ConnectionError:
            error_msg = f"Не удается подключиться к модели по адресу {self.api_url}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "response": ""
            }

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP ошибка: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "response": ""
            }
