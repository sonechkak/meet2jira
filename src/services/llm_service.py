import logging

import httpx as requests

from src.pipeline.elements.base import Element
from src.schemas.llm.llm_service_schemas import LLMServiceResponseSchema

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LlmService(Element):
    """Сервис для ламы."""

    def __init__(
        self, prompt: str, model="yandex-gpt", base_url="http://localhost:11434"
    ) -> None:
        """Инициализация сервиса LLM."""

        logger.debug(
            "Инициализация LLM сервиса с моделью %s и базовым URL %s", model, base_url
        )
        super().__init__(model=model, tools=[], prompt="", obj=None)
        self.prompt = prompt
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"

    def run(self) -> LLMServiceResponseSchema:
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
                },
            }

            logger.info(f"Отправка запроса к модели: {self.api_url}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120,
            )

            logger.debug("Запрос отправлен, ожидаем ответа...")
            response.raise_for_status()
            logger.info("Ответ получен успешно.")

            response_data = response.json()
            generated_text = response_data.get("response", "")

            if generated_text and generated_text.strip():
                cleaned_text = generated_text.strip()
                logger.debug(f"Получен ответ длиной {len(cleaned_text)} символов.")
                logger.debug("Ответ успешно обработан.")
                return LLMServiceResponseSchema(
                    status="success",
                    response_text=cleaned_text,
                    response_data=response_data,
                    model_name=self.model,
                )
            else:
                logger.error("Модель вернула пустой ответ.")
                return LLMServiceResponseSchema(
                    status="error",
                    error=True,
                    error_message="Модель вернула пустой ответ. Проверьте настройки модели и запрос.",
                    response_text="",
                )

        except Exception as e:
            logger.error(f"Ошибка при вызове API model: {str(e)}")
            return LLMServiceResponseSchema(
                status="error", error=True, error_message=str(e), response_text=""
            )
