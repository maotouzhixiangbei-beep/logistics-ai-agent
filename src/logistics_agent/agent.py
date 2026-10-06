"""Pydantic AI Agent：把业务系统封装成 Function Calling 工具。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from pydantic_ai import Agent, ModelRetry, RunContext

from .models import InventoryItem, Order, Shipment, ShipmentBooking
from .wms_client import WmsClient


@dataclass
class AgentDeps:
    wms: WmsClient


SYSTEM_PROMPT = """\
你是物流供应链运营团队的 AI 助手，服务仓储（WMS）、订单（OMS）和运输（TMS）业务。

你只能通过调用工具访问业务系统，不要凭空编造库存、订单或运单数据：
- 查库存 -> query_inventory
- 查订单 -> query_order
- 为订单开运单/发货 -> create_shipment
- 查运输状态 -> track_shipment

规则：
1. 用户问到库存/订单/运单时，先用对应工具取真实数据再回答。
2. 回答使用中文，面向运营人员，简洁、直接。
3. 引用工具返回里的 SKU、仓库、订单号、运单号、数量要准确，不要改动。
4. 数据不足（如查不到）时，如实说明找不到，不要猜测。
"""

_TOOLS: list = []
_agent_instance: Agent | None = None


def _tool(func):
    _TOOLS.append(func)
    return func


def get_agent() -> Agent:
    """懒加载 Agent 实例：仅在实际需要时创建，避免模块导入时就要求 API key。"""
    global _agent_instance
    if _agent_instance is not None:
        return _agent_instance
    model = os.getenv("LOGISTICS_AGENT_MODEL", "deepseek:deepseek-chat")
    agent_inst = Agent(
        model,
        deps_type=AgentDeps,
        instructions=SYSTEM_PROMPT,
    )
    for t in _TOOLS:
        agent_inst.tool(t)
    _agent_instance = agent_inst
    return agent_inst


@_tool
async def query_inventory(
    ctx: RunContext[AgentDeps], sku: str, warehouse: str | None = None
) -> InventoryItem:
    """查询某个 SKU 的库存（在库、已占用、可用数量）。warehouse 可选，指定仓库。"""
    try:
        return await ctx.deps.wms.get_inventory(sku, warehouse)
    except LookupError:
        raise ModelRetry(f"没有找到 SKU={sku} 的库存，请确认 SKU 或仓库后重试")


@_tool
async def query_order(ctx: RunContext[AgentDeps], order_id: str) -> Order:
    """按订单号查询 OMS 订单明细与当前状态。"""
    try:
        return await ctx.deps.wms.get_order(order_id)
    except LookupError:
        raise ModelRetry(f"没有找到订单 {order_id}，请确认订单号后重试")


@_tool
async def track_shipment(ctx: RunContext[AgentDeps], tracking_no: str) -> Shipment:
    """按运单号查询 TMS 运输状态与当前位置/预计送达时间。"""
    try:
        return await ctx.deps.wms.track_shipment(tracking_no)
    except LookupError:
        raise ModelRetry(f"没有找到运单 {tracking_no}，请确认运单号后重试")


@_tool
async def create_shipment(ctx: RunContext[AgentDeps], booking: ShipmentBooking) -> Shipment:
    """为已存在的订单创建 TMS 运单，进入发货流程。返回新生成的运单。"""
    try:
        return await ctx.deps.wms.create_shipment(booking)
    except LookupError:
        raise ModelRetry(f"订单 {booking.order_id} 不存在，无法开运单，请先查询订单确认")
