from src.pipeline.elements.base import Tool


class DocumentClassifier(Tool):
    """Простой класс для классификации документов."""

    def __init__(self,
                 name: str = "DocumentClassifier",
                 description: str = "Классифицирует документ на основе его содержимого",
                 **kwargs):
        super().__init__(name=name, description=description, **kwargs)
        self.document_content = kwargs.get('document_content', '')

    def run(self) -> str:
        """Классифицирует документ на основе его содержимого."""
        if not self.document_content or not self.document_content.strip():
            return "other"

        text_lower = self.document_content.lower()

        # Подсчитываем количество ключевых слов для каждой категории
        financial_count = self._count_financial_words(text_lower)
        medical_count = self._count_medical_words(text_lower)
        academic_count = self._count_academic_words(text_lower)
        technical_count = self._count_technical_words(text_lower)

        # Создаем словарь с результатами
        scores = {
            "financial": financial_count,
            "medical": medical_count,
            "academic": academic_count,
            "technical": technical_count
        }

        # Находим категорию с максимальным количеством слов
        max_category = max(scores, key=scores.get)
        max_count = scores[max_category]

        # Если найдено меньше 2 ключевых слов, возвращаем "other"
        if max_count < 2:
            return "other"

        return max_category

    def _count_financial_words(self, text_lower: str) -> int:
        """Считает финансовые ключевые слова."""
        keywords = [
            "деньги", "рубл", "доллар", "евро", "сумма", "платеж", "оплата",
            "счет", "выписка", "банк", "кредит", "депозит", "процент",
            "прибыль", "убыток", "доход", "расход", "бюджет", "налог",
            "финанс", "стоимость", "цена", "тариф", "баланс", "отчет"
        ]

        count = 0
        for word in keywords:
            count += text_lower.count(word)
        return count

    def _count_medical_words(self, text_lower: str) -> int:
        """Считает медицинские ключевые слова."""
        keywords = [
            "пациент", "больной", "диагноз", "лечение", "терапия", "врач",
            "доктор", "медицинский", "клиника", "больница", "поликлиника",
            "рецепт", "лекарство", "препарат", "болезнь", "симптом",
            "здоровье", "медицина", "анализ", "обследование", "операция"
        ]

        count = 0
        for word in keywords:
            count += text_lower.count(word)
        return count

    def _count_academic_words(self, text_lower: str) -> int:
        """Считает академические ключевые слова."""
        keywords = [
            "исследование", "изучение", "анализ", "эксперимент", "наука",
            "научный", "теория", "гипотеза", "метод", "результат",
            "вывод", "заключение", "студент", "университет", "институт",
            "диссертация", "статья", "работа", "проект", "курсовая",
            "дипломная", "выпускная", "вкр", "академический", "образование"
        ]

        count = 0
        for word in keywords:
            count += text_lower.count(word)
        return count

    def _count_technical_words(self, text_lower: str) -> int:
        """Считает технические ключевые слова."""
        keywords = [
            "техничес", "технология", "система", "устройство", "оборудование",
            "механизм", "схема", "чертеж", "инструкция", "руководство",
            "спецификация", "параметр", "характеристика", "функция",
            "процесс", "операция", "настройка", "установка", "ремонт",
            "обслуживание", "программа", "софт", "железо", "компьютер"
        ]

        count = 0
        for word in keywords:
            count += text_lower.count(word)
        return count

    def get_classification_details(self) -> dict:
        """Возвращает детали классификации для отладки."""
        if not hasattr(self, '_last_scores'):
            text_lower = self.document_content.lower()
            self._last_scores = {
                "financial": self._count_financial_words(text_lower),
                "medical": self._count_medical_words(text_lower),
                "academic": self._count_academic_words(text_lower),
                "technical": self._count_technical_words(text_lower)
            }
        return self._last_scores

    def __str__(self):
        return f"{self.__class__.__name__}({self.get_classification_details()})"