from typing import Optional, Type, Any

from temporalio.converter import PayloadCodec
from temporalio.worker import Interceptor, WorkflowInterceptorClassInput, WorkflowInboundInterceptor, \
    ActivityInboundInterceptor, ExecuteActivityInput

from large_payload._activity import LargePayloadActivityImpl
from large_payload.store import LargePayloadStore


class LargePayloadActivityInboundInterceptor(ActivityInboundInterceptor):
    def __init__(self, next: ActivityInboundInterceptor, store: LargePayloadStore):
        super.__init__(next)
        self.store = store

    async def execute_activity(self, input: ExecuteActivityInput) -> Any:
        return await super().execute_activity(input)


class LargePayloadInterceptor(Interceptor):
    def __init__(self, store: LargePayloadStore, codec: PayloadCodec = None) -> None:
        if store is None:
            raise ValueError("store is required")
        self.store = store
        self.activity_impl = LargePayloadActivityImpl(store=store, codec=codec)

    def intercept_activity(self, next: ActivityInboundInterceptor) -> ActivityInboundInterceptor:
        return LargePayloadActivityInboundInterceptor(next, self.activity_impl)

    def workflow_interceptor_class(self, input: WorkflowInterceptorClassInput) -> Optional[
        Type[WorkflowInboundInterceptor]]:
        return super().workflow_interceptor_class(input)
