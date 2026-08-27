from __future__ import annotations

from dataclasses import dataclass

TASK_QUEUE = "external-workflow-streams-sample"
INPUT_STREAM_NAME = "messages"
OUTPUT_STREAM_NAME = "processed-messages"


@dataclass(frozen=True)
class StreamMessage:
    sequence: int
    body: str


@dataclass(frozen=True)
class ProcessedMessage:
    sequence: int
    body: str
