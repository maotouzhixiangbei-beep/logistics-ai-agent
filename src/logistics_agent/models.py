"""物流领域模型：作为 Function Calling 工具的入参与返回结构。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    """WMS 库存记录（查库存工具的返回）。"""

    sku: str = Field(description="商品 SKU 编码")
    description: str = Field(description="商品名称")
    warehouse: str = Field(description="所在仓库编码")
    on_hand: int = Field(description="在库数量")
    allocated: int = Field(description="已被订单占用的数量")
    available: int = Field(description="可售/可用数量")
    unit: str = Field(description="计量单位")


class OrderLine(BaseModel):
    """OMS 订单的单个明细行。"""

    sku: str = Field(description="商品 SKU")
    quantity: int = Field(description="下单数量")


class Order(BaseModel):
    """OMS 订单（查订单工具的返回）。"""

    order_id: str = Field(description="订单号")
    customer: str = Field(description="客户名称")
    status: Literal[
        "created", "allocated", "picked", "shipped", "delivered", "cancelled"
    ] = Field(description="订单当前状态")
    warehouse: str = Field(description="发货仓库编码")
    lines: list[OrderLine] = Field(description="订单明细")
    tracking_no: str | None = Field(
        default=None, description="关联运单号（若已发货则有值，可用于查运输进度）"
    )


class Shipment(BaseModel):
    """TMS 运单（开运单 / 查运输工具的返回）。"""

    tracking_no: str = Field(description="运单号")
    order_id: str = Field(description="关联订单号")
    carrier: str = Field(description="承运商")
    status: Literal[
        "booked", "in_transit", "out_for_delivery", "delivered", "exception"
    ] = Field(description="运输状态")
    current_location: str = Field(description="当前所在位置 / 节点")
    eta: datetime | None = Field(default=None, description="预计送达时间")


class ShipmentBooking(BaseModel):
    """开运单工具的入参（单对象参数，schema 会被自动展开）。"""

    order_id: str = Field(description="要发货的订单号")
    carrier: str = Field(description="承运商，例如 顺丰速运 / 京东物流")
