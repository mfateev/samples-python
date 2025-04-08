from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type, Any, Callable, Awaitable

from temporalio.converter import PayloadCodec

from large_payload.reference import JSONType, T, U
from large_payload.store import LargePayloadStore


class _LargePayloadImpl(ABC):
    def __init__(self, store: LargePayloadStore, codec: PayloadCodec):
        self._store = store
        self._codec: PayloadCodec = codec

    @abstractmethod
    async def fetch(self, encoded_ref: JSONType, type_hint=Type[T]) -> T:
        pass

    @abstractmethod
    async def store(self, value: Any) -> JSONType:
        """
        Stores a value in an external store.
        The returned reference can be used to fetch the payload back.
        """
        pass

    async def extract(self, encoded_ref: JSONType, transformer: Callable[[T], Awaitable[U]]) -> U:
        pass
