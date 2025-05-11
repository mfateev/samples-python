from __future__ import annotations as _annotations

from typing import Optional

from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import Usage
from temporalio import activity


class PydanticModelInput(BaseModel):
    model_name: str
    model_config = {
        "arbitrary_types_allowed": True
    }
    messages: list[ModelMessage]
    model_settings: Optional[ModelSettings]
    model_request_parameters: ModelRequestParameters


class PydanticModelOutput(BaseModel):
    model_config = {
        "arbitrary_types_allowed": True
    }
    model_response: ModelResponse
    usage: Usage


@activity.defn
async def invoke_pydantic_model_activity(model_input: PydanticModelInput) -> PydanticModelOutput:
    model = OpenAIResponsesModel(model_name=model_input.model_name)
    response, usage = await model.request(
        messages=model_input.messages,
        model_settings=model_input.model_settings,
        model_request_parameters=model_input.model_request_parameters
    )
    return PydanticModelOutput(model_response=response, usage=usage)
