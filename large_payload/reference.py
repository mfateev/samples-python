import contextlib
import contextvars
from abc import ABC
from dataclasses import dataclass, field
from typing import Generic, TypeVar, ClassVar, Type, Callable, Awaitable, Any, get_origin, Union, List, Dict

from large_payload._impl import LargePayloadImpl

T = TypeVar('T')
U = TypeVar('U')

JSONType = Union[
    None,
    bool,
    int,
    float,
    str,
    List["JSONType"],
    Dict[str, "JSONType"]
]


@dataclass
class LargePayloadRef(ABC, Generic[T]):
    _impl_context: ClassVar[contextvars.ContextVar[LargePayloadImpl]] = contextvars.ContextVar(
        '_large_payload_store')

    @classmethod
    @contextlib.contextmanager
    def use_impl(cls, impl_instance: LargePayloadImpl):
        token = cls._impl_context.set(impl_instance)
        try:
            yield
        finally:
            cls._impl_context.reset(token)

    # Encoded payload reference
    _reference: JSONType = None

    # Deserialized payload
    _value: T = None
    _value_set: bool = False

    def __init__(self, value: T) -> None:
        self._value = value
        self._value_set = True

    async def fetch(self, type_hint=Type[T]) -> T:
        """
        Fetch and return the payload.
        Avoid calling in the context of a workflow as it can affect the replay performance.
        Use :meth:`extract` instead.
        """
        if self._value_set:
            return self._value

        impl: LargePayloadImpl = LargePayloadRef._impl_context.get()
        return await impl.fetch(encoded_ref=self._reference, type_hint=type_hint)

    async def extract(self, transformer: Callable[[T], Awaitable[U]]) -> U:
        """
        Applies a transformer function to the payload.
        When called in the context of a workflow the result of the transformer function
        is used when workflow is replayed.

        Args:
            transformer: A function that takes the payload of type T
                         and returns a transformed value of type U.

        Returns:
            The transformed payload of type U.
        """
        impl: LargePayloadImpl = LargePayloadRef._impl_context.get()
        return await impl.extract(transformer=transformer, encoded_ref=self._reference)
