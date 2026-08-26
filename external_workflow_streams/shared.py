from __future__ import annotations

from dataclasses import dataclass

TASK_QUEUE = "external-workflow-streams-sample"
STREAM_NAME = "messages"


@dataclass(frozen=True)
class StreamMessage:
    sequence: int
    body: str
