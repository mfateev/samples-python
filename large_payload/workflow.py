from typing import Any, Type, TypeVar

from temporalio import activity, workflow
from temporalio.converter import PayloadCodec

from large_payload.reference import LargePayloadImpl, LargePayloadStore

T = TypeVar('T')


class LargePayloadWorkflowImpl(LargePayloadImpl):
    def __init__(self, store: LargePayloadStore, codec: PayloadCodec):
        self.store = store
        self.codec: PayloadCodec = codec

    async def fetch(self, reference: Any, type_hint=Type[T]) -> T:
        raw_payload = await self.store.fetch(reference)
        decoded = await self.codec.decode([raw_payload])
        value = workflow.payload_converter().from_payload(decoded, type_hint=type_hint)
        return value

    async def store(self, value: Any) -> Any:
        payload = workflow.payload_converter().to_payload(value)
        encoded = await self.codec.encode([payload])
        return await self.store.store(encoded[0])
