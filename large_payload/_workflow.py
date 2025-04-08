from datetime import timedelta
from typing import Any, Type, TypeVar, Callable, Awaitable, get_origin

from temporalio import activity, workflow
from temporalio.common import RawValue
from temporalio.converter import PayloadCodec
from temporalio.workflow import unsafe

from large_payload.reference import JSONType, U
from large_payload.store import LargePayloadStore
from large_payload._impl import _LargePayloadImpl

T = TypeVar('T')


class _LargePayloadWorkflowImpl(_LargePayloadImpl):

    async def fetch(self, reference: Any, type_hint=Type[T]) -> T:
        raw_payload = await self._store.fetch(reference)
        decoded = await self._codec.decode([raw_payload])
        value = workflow.payload_converter().from_payload(decoded, type_hint=type_hint)
        return value

    async def store(self, value: Any) -> Any:
        payload = workflow.payload_converter().to_payload(value)
        encoded = await self._codec.encode([payload])
        return await self._store.store(encoded[0])

    async def extract(self, encoded_ref: JSONType, transformer: Callable[[T], Awaitable[U]]) -> U:
        # We really need the side-effect here.
        # The non-deterministic code relies on the lack of check of the activity input.
        value = None
        if not unsafe.is_replaying():
            with workflow.unsafe.sandbox_unrestricted():
                value = await transformer(self.fetch(reference=encoded_ref, type_hint=get_origin(transformer)))
        return workflow.execute_local_activity(_LargePayloadWorkflowImpl.extract, value,
                                               start_to_close_timeout=timedelta(seconds=10))

    @classmethod
    @activity.defn
    async def extract(cls, value: RawValue) -> RawValue:
        return value
