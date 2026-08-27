from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.contrib.external_workflow_streams import (
    external_output_stream,
    external_stream,
)

from external_workflow_streams.shared import (
    INPUT_STREAM_NAME,
    OUTPUT_STREAM_NAME,
    ProcessedMessage,
    StreamMessage,
)


@workflow.defn
class MessageConsumerWorkflow:
    """Consume externally stored messages without putting them in History."""

    @workflow.run
    async def run(self, expected_messages: int) -> int:
        messages = external_stream.with_options(
            idle_timeout=timedelta(seconds=2)
        ).topic(INPUT_STREAM_NAME, type=StreamMessage)
        processed_messages = external_output_stream.topic(
            OUTPUT_STREAM_NAME, type=ProcessedMessage
        )
        subscription = messages.subscribe()

        received = 0
        async for message in subscription:
            workflow.logger.info(
                "Received external stream message %s: %s",
                message.sequence,
                message.body,
            )
            await processed_messages.publish(
                ProcessedMessage(
                    sequence=message.sequence,
                    body=message.body.upper(),
                )
            )
            received += 1
            if received == expected_messages:
                subscription.close()
                break

        await processed_messages.finish()
        return received
