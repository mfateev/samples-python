from __future__ import annotations

import os

from temporalio.contrib.external_workflow_streams import RedisStreamBackend

REDIS_URL_ENV = "TEMPORAL_STREAMS_REDIS_URL"


def create_backend() -> RedisStreamBackend:
    """Create the backend shared by the Worker, producer, and output client."""
    return RedisStreamBackend(
        url=os.getenv(REDIS_URL_ENV, "redis://localhost:6379/0"),
        key_prefix="temporal-samples:external-workflow-streams",
    )
