from dataclasses import dataclass


@dataclass
class ParsedTask:
    task_id: str
    title: str
    # priority: str
    # assignee: str
    time_estimate: str
    description: str
    acceptance_criteria: list[str]
    dependencies: list[str]
