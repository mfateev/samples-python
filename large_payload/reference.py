from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Any, Type, Callable, Awaitable

from temporalio.api.common.v1 import Payload
from temporalio.converter import PayloadCodec

from large_payload.large_payload_ref import JSONType, T, U


class LargePayloadStore(ABC):
    @abstractmethod
    async def fetch(self, encoded_ref: JSONType) -> Payload:
        pass

    @abstractmethod
    async def store(self, payload: Payload) -> JSONType:
        """
        Stores payload. The returned reference can be used to fetch the payload back.
        """
        pass


class LargePayloadImpl(ABC):
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
