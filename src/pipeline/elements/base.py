from typing import Any


class Element:
    """Класс для представления элемента, который может быть выполнен с использованием модели и инструментов."""
    def __init__(self, model: str, tools: list, prompt: str, obj: Any):
        self.model = model
        self.tools = tools
        self.prompt = prompt
        self.obj = obj

    def __call__(self, *args, **kwargs):
        return self.run()

    def run(self) -> dict:
        raise NotImplementedError("Метод run должен быть реализован в подклассе.")


class Pipeline(Element):
    """Класс для представления конвейера, который выполняет последовательность элементов."""
    def __init__(self, model: str, tools: list, elements: list):
        super().__init__(model, tools, '', None)
        self.document_type = None
        self.elements = elements

    def run(self) -> dict:
        """Выполняет все элементы конвейера."""
        results = []
        for element in self.elements:
            result = element.run()
            results.append(result)
        return {'results': results}

    def __str__(self):
        return f'Pipeline: {self.model} with elements {len(self.elements)}'


class Tool:
    """Класс для представления инструмента, который может быть использован в конвейере."""
    def __init__(self, name: str, description: str, **kwargs):
        self.name = name
        self.description = description
        self.kwargs = kwargs

    def run(self) -> Any:
        """Метод для выполнения действия инструмента."""
        raise NotImplementedError("Метод run должен быть реализован в подклассе.")

    def __str__(self):
        return f'Tool: {self.name} - {self.description}'
