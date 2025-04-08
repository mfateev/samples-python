from typing import Optional, Type, Any

from temporalio import workflow, worker
from temporalio.converter import PayloadCodec
from temporalio.worker import Interceptor, WorkflowInterceptorClassInput, WorkflowInboundInterceptor, \
    ActivityInboundInterceptor, ExecuteActivityInput, HandleUpdateInput, HandleQueryInput, HandleSignalInput, \
    ExecuteWorkflowInput
from temporalio.worker._workflow_instance import _WorkflowExternFunctions

from large_payload._activity import LargePayloadActivityImpl
from large_payload._impl import LargePayloadImpl
from large_payload._workflow import LargePayloadWorkflowImpl
from large_payload.reference import LargePayloadRef
from large_payload.store import LargePayloadStore


class LargePayloadActivityInboundInterceptor(ActivityInboundInterceptor):
    def __init__(self, next: ActivityInboundInterceptor, impl: LargePayloadImpl):
        super.__init__(next)
        self._impl = impl

    async def execute_activity(self, input: ExecuteActivityInput) -> Any:
        with LargePayloadRef.use_impl(self._impl):
            return await super().execute_activity(input)


class LargePayloadWorkflowInboundInterceptor(WorkflowInboundInterceptor):

    def __init__(self, next: worker.WorkflowInboundInterceptor) -> None:
        super().__init__(next)
        self._impl = workflow.extern_functions()["__temporal_large_payload_workflow_impl"]()


    async def execute_workflow(self, input: ExecuteWorkflowInput) -> Any:
        with LargePayloadRef.use_impl(self._impl):
            return await super().execute_workflow(input)


    async def handle_signal(self, input: HandleSignalInput) -> None:
        with LargePayloadRef.use_impl(self._impl):
            return await super().handle_signal(input)


    async def handle_query(self, input: HandleQueryInput) -> Any:
        with LargePayloadRef.use_impl(self._impl):
            return await super().handle_query(input)


    def handle_update_validator(self, input: HandleUpdateInput) -> None:
        with LargePayloadRef.use_impl(self._impl):
            super().handle_update_validator(input)


    async def handle_update_handler(self, input: HandleUpdateInput) -> Any:
        with LargePayloadRef.use_impl(self._impl):
            return await super().handle_update_handler(input)


class LargePayloadInterceptor(Interceptor):
    def __init__(self, store: LargePayloadStore, codec: PayloadCodec = None) -> None:
        if store is None:
            raise ValueError("store is required")
        self._activity_impl = LargePayloadActivityImpl(store=store, codec=codec)
        self._workflow_impl = LargePayloadWorkflowImpl(store=store, codec=codec)

    def get_workflow_impl(self) -> Any:
        return self._workflow_impl

    def intercept_activity(self, next: ActivityInboundInterceptor) -> ActivityInboundInterceptor:
        return LargePayloadActivityInboundInterceptor(next, self._activity_impl)

    def workflow_interceptor_class(self, input: WorkflowInterceptorClassInput) -> Optional[
        Type[WorkflowInboundInterceptor]]:
        input.unsafe_extern_functions["__temporal_large_payload_workflow_impl"] = self.get_workflow_impl()
        return LargePayloadWorkflowInboundInterceptor
