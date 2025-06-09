"""
DataConverter that supports conversion of types used by OpenAI Agents SDK.
These are mostly Pydantic types. NotGiven requires special handling.
"""
from __future__ import annotations

import json
from typing import Any, Optional, Type, TypeVar, List, get_origin, get_args

import temporalio.api.common.v1
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict
from pydantic import RootModel, TypeAdapter, BaseModel
from temporalio.converter import (
    CompositePayloadConverter,
    DataConverter,
    DefaultPayloadConverter,
    EncodingPayloadConverter,
    JSONPlainPayloadConverter,
)

T = TypeVar("T", bound=BaseModel)


class _WrapperModel(RootModel[T]):
    model_config = {
        "arbitrary_types_allowed": True,
    }


def _postprocess_messages(obj):
    if isinstance(obj, list) and all(isinstance(i, BaseMessage) for i in obj):
        return messages_to_dict(obj)
    return obj

class _PydanticPlusJSONPlainPayloadConverter(EncodingPayloadConverter):
    """Pydantic JSON payload converter.

    Supports conversion of all types supported by Pydantic to and from JSON.

    In addition to Pydantic models, these include all `json.dump`-able types,
    various non-`json.dump`-able standard library types such as dataclasses,
    types from the datetime module, sets, UUID, etc, and custom types composed
    of any of these.

    See https://docs.pydantic.dev/latest/api/standard_library_types/
    """

    @property
    def encoding(self) -> str:
        """See base class."""
        return "json/plain"

    def to_payload(self, value: Any) -> Optional[temporalio.api.common.v1.Payload]:
        """See base class.
        Needs _WrapperModel configure arbitrary_types_allowed=True
        """

        # if isinstance(value, list) and all(isinstance(v, BaseMessage) for v in value):
        #     tree = messages_to_dict(value)
        #     data = json.dumps(tree).encode()
        # else:
        # wrapper = _WrapperModel[type(processed)](root=processed)
        wrapper = _WrapperModel[Any](root=value)
        data = wrapper.model_dump_json().encode()
        # tree = wrapper.model_dump()

        # tree = _postprocess_messages(tree)
        # data = json.dumps(tree).encode()


        # if isinstance(value, list) and all(isinstance(v, BaseMessage) for v in value):
        #     tree = messages_to_dict(value)
        #     data = json.dumps(tree).encode()
        # else:
        #     wrapper = _WrapperModel[type(value)](root=value)
        #     data = wrapper.model_dump_json().encode()

        return temporalio.api.common.v1.Payload(
            metadata={"encoding": self.encoding.encode()}, data=data
        )

    def from_payload(
            self,
            payload: temporalio.api.common.v1.Payload,
            type_hint: Optional[Type] = None,
    ) -> Any:
        _type_hint = type_hint if type_hint is not None else Any
        wrapper = _WrapperModel[_type_hint]

        # Explicit conversion of polymorphic BaseMessage types
        if get_origin(_type_hint) is list and get_args(_type_hint) == (BaseMessage,):
            tree = json.loads(payload.data.decode())
            # tree = TypeAdapter(wrapper).validate_json(payload.data.decode())
            # noinspection PyTypeChecker
            return messages_from_dict(tree)

        # Needed due to
        # if TYPE_CHECKING:
        #     from .agent import Agent
        #
        # in the agents/items.py
        # wrapper.model_rebuild(
        #     _types_namespace={
        #         "TResponseOutputItem": TResponseOutputItem,
        #         "Usage": Usage,
        #     }
        # )
        return TypeAdapter(wrapper).validate_json(payload.data.decode()).root


class PydanticPlusPayloadConverter(CompositePayloadConverter):
    """Payload converter for payloads containing pydantic model instances.

    JSON conversion is replaced with a converter that uses
    :py:class:`PydanticJSONPlainPayloadConverter`.
    """

    def __init__(self) -> None:
        """Initialize object"""
        json_payload_converter = _PydanticPlusJSONPlainPayloadConverter()
        super().__init__(
            *(
                c
                if not isinstance(c, JSONPlainPayloadConverter)
                else json_payload_converter
                for c in DefaultPayloadConverter.default_encoding_payload_converters
            )
        )


pydantic_plus_converter = DataConverter(payload_converter_class=PydanticPlusPayloadConverter)
"""Pydantic data converter that supports non pydantic model like typed map as root type."""
