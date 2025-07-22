import logging
import openai


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка клиента для модели
client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="yandex-gpt"
)

# Запрос к модели
response = client.chat.completions.create(
    model="hf.co/yandex/YandexGPT-5-Lite-8B-instruct-GGUF:Q4_K_M",
    messages=[
        {"role": "user", "content": "Привет! Ты говоришь по-русски?"}
    ],
    max_tokens=512,
    temperature=0.7
)

logger.info(response)