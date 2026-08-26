from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.contrib.external_workflow_streams import external_stream

from external_workflow_streams.shared import STREAM_NAME, StreamMessage


@workflow.defn
class MessageConsumerWorkflow:
    """Consume externally stored messages without putting them in History."""

    @workflow.run
    async def run(self, expected_messages: int) -> int:
        messages = external_stream.with_options(
            idle_timeout=timedelta(seconds=2)
        ).topic(STREAM_NAME, type=StreamMessage)
        subscription = messages.subscribe()

        received = 0
        async for message in subscription:
            workflow.logger.info(
                "Received external stream message %s: %s",
                message.sequence,
                message.body,
            )
            received += 1
            if received == expected_messages:
                subscription.close()
                return received

        return received
