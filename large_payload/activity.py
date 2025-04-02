from typing import Any, Type, TypeVar, Callable, Awaitable, get_origin

from dulwich.porcelain import fetch
from temporalio import activity
from temporalio.converter import PayloadCodec

from large_payload.large_payload_ref import JSONType, U, T
from large_payload.reference import LargePayloadImpl, LargePayloadStore


class LargePayloadActivityImpl(LargePayloadImpl):

    async def fetch(self, reference: JSONType, type_hint=Type[T]) -> T:
        raw_payload = await self._store.fetch(reference)
        decoded = await self._codec.decode([raw_payload])
        value = activity.payload_converter().from_payload(decoded, type_hint=type_hint)
        return value

    async def store(self, value: Any) -> JSONType:
        payload = activity.payload_converter().to_payload(value)
        encoded = await self._codec.encode([payload])
        return await self._store.store(encoded[0])

    async def extract(self, encoded_ref: JSONType, transformer: Callable[[T], Awaitable[U]]) -> U:
        return await transformer(self.fetch(reference=encoded_ref, type_hint=get_origin(transformer)))

