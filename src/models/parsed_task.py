from dataclasses import dataclass
from typing import List


@dataclass
class ParsedTask:
    task_id: str
    title: str
    # priority: str
    # assignee: str
    time_estimate: str
    description: str
    acceptance_criteria: List[str]
    dependencies: List[str]
