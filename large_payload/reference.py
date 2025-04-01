from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Any, Type

from temporalio.api.common.v1 import Payload

T = TypeVar('T')
U = TypeVar('U')


class LargePayloadStore(ABC):
    @abstractmethod
    async def fetch(self, encoded_ref: Any) -> Payload:
        pass

    @abstractmethod
    async def store(self, payload: Payload) -> Any:
        """
        Stores payload. The returned reference can be used to fetch the payload back.
        The result must be serializable using the configured data converter.
        """
        pass


class LargePayloadImpl(ABC):
    @abstractmethod
    async def fetch(self, encoded_ref: Any, type_hint=Type[T]) -> T:
        pass

    @abstractmethod
    async def store(self, value: Any) -> Any:
        """
        Stores a value in an external store.
        The returned reference can be used to fetch the payload back.
        The result is serializable using the configured data converter.
        """
        pass
