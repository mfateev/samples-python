from __future__ import annotations

from abc import ABC, abstractmethod

from temporalio.api.common.v1 import Payload

from large_payload.reference import JSONType


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


