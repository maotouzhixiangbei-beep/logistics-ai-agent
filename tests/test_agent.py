"""Agent 测试：用 FunctionModel / TestModel 替代真实 LLM，无需 API key。"""

from pydantic_ai import ModelMessage, ModelResponse, TextPart, ToolCallPart, models
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.test import TestModel

from logistics_agent.agent import AgentDeps, get_agent
from logistics_agent.models import InventoryItem, Order, Shipment
from logistics_agent.wms_client import InMemoryWmsClient

models.ALLOW_MODEL_REQUESTS = False

agent = get_agent()


def _deps():
    return AgentDeps(wms=InMemoryWmsClient())


def _inventory_flow(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    if len(messages) == 1:
        return ModelResponse(
            parts=[ToolCallPart("query_inventory", {"sku": "SKU-1001", "warehouse": "WH-SH"})]
        )
    msg = messages[-1].parts[0]
    assert msg.part_kind == "tool-return"
    return ModelResponse(parts=[TextPart(f"库存查询结果：{msg.content}")])


def _order_flow(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    if len(messages) == 1:
        return ModelResponse(parts=[ToolCallPart("query_order", {"order_id": "ORD-1002"})])
    msg = messages[-1].parts[0]
    assert msg.part_kind == "tool-return"
    return ModelResponse(parts=[TextPart(f"订单查询结果：{msg.content}")])


def test_agent_calls_inventory_tool_and_uses_real_seed_data():
    with agent.override(model=FunctionModel(_inventory_flow)):
        result = agent.run_sync("SKU-1001 在上海仓还有多少可用库存？", deps=_deps())
    assert "SKU-1001" in result.output
    assert "WH-SH" in result.output
    assert "85" in result.output


def test_agent_calls_order_tool_and_uses_real_seed_data():
    with agent.override(model=FunctionModel(_order_flow)):
        result = agent.run_sync("ORD-1002 现在什么状态？", deps=_deps())
    assert "ORD-1002" in result.output
    assert "shipped" in result.output


class _StubWms:
    async def get_inventory(self, sku, warehouse=None):
        return InventoryItem(sku=sku, description="demo", warehouse="WH-X",
                             on_hand=10, allocated=1, available=9, unit="箱")

    async def get_order(self, order_id):
        return Order(order_id=order_id, customer="c", status="created",
                     warehouse="WH-X", lines=[])

    async def create_shipment(self, booking):
        return Shipment(tracking_no="TRK-1", order_id=booking.order_id, carrier=booking.carrier,
                        status="booked", current_location="待揽收", eta=None)

    async def track_shipment(self, tracking_no):
        return Shipment(tracking_no=tracking_no, order_id="ORD-1", carrier="c",
                        status="booked", current_location="待揽收", eta=None)


def test_agent_runs_end_to_end_with_test_model():
    with agent.override(model=TestModel()):
        result = agent.run_sync("帮我看看库存情况", deps=AgentDeps(wms=_StubWms()))
    assert isinstance(result.output, str)
    assert result.output
