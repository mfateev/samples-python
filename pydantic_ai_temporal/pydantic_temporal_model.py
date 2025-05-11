from __future__ import annotations as _annotations

from datetime import timedelta

from pydantic_ai import models
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import Usage
from temporalio import workflow

from pydantic_ai_temporal import invoke_pydantic_model_activity
from pydantic_ai_temporal.invoke_pydantic_model_activity import PydanticModelInput


class TemporalPydanticModel(models.Model):
    _model_name: str

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    async def request(self, messages: list[ModelMessage], model_settings: ModelSettings | None,
                      model_request_parameters: ModelRequestParameters) -> tuple[ModelResponse, Usage]:
        model_input = PydanticModelInput(
            model_name=self._model_name,
            messages=messages,
            model_settings=model_settings,
            model_request_parameters=model_request_parameters,
        )
        result = await workflow.execute_activity(invoke_pydantic_model_activity, model_input,
                                                 start_to_close_timeout=timedelta(seconds=60))
        return result.model_response, result.usage

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def system(self) -> str | None:
        return 'openai'
