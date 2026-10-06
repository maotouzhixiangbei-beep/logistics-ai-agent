"""WMS/OMS/TMS 业务系统客户端（统一接口 + HTTP/内存两种实现）。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol

import httpx

from .models import InventoryItem, Order, Shipment, ShipmentBooking
from .seed import INVENTORY_ROWS, ORDER_ROWS, SHIPMENT_ROWS


_WAREHOUSE_ALIAS: dict[str, str] = {
    "WH-SH": "WH-SH", "wh-sh": "WH-SH", "上海仓": "WH-SH", "上海": "WH-SH",
    "华东仓": "WH-SH",
    "WH-SZ": "WH-SZ", "wh-sz": "WH-SZ", "深圳仓": "WH-SZ", "深圳": "WH-SZ",
    "华南仓": "WH-SZ",
}


def normalize_warehouse(warehouse: str | None) -> str | None:
    """把中文别名（上海仓 / 深圳仓）统一成仓库编码（WH-SH / WH-SZ）。"""
    if warehouse is None:
        return None
    key = warehouse.strip()
    return _WAREHOUSE_ALIAS.get(key, key)


class WmsClient(Protocol):
    async def get_inventory(self, sku: str, warehouse: str | None = None) -> InventoryItem: ...
    async def get_order(self, order_id: str) -> Order: ...
    async def create_shipment(self, booking: ShipmentBooking) -> Shipment: ...
    async def track_shipment(self, tracking_no: str) -> Shipment: ...


class HttpWmsClient:
    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=10.0,
            trust_env=False,
        )

    async def get_inventory(self, sku: str, warehouse: str | None = None) -> InventoryItem:
        params = {"warehouse": normalize_warehouse(warehouse)} if warehouse is not None else None
        resp = await self._client.get(f"/inventory/{sku}", params=params)
        resp.raise_for_status()
        return InventoryItem.model_validate(resp.json())

    async def get_order(self, order_id: str) -> Order:
        resp = await self._client.get(f"/orders/{order_id}")
        resp.raise_for_status()
        return Order.model_validate(resp.json())

    async def create_shipment(self, booking: ShipmentBooking) -> Shipment:
        resp = await self._client.post("/shipments", json=booking.model_dump())
        resp.raise_for_status()
        return Shipment.model_validate(resp.json())

    async def track_shipment(self, tracking_no: str) -> Shipment:
        resp = await self._client.get(f"/shipments/{tracking_no}")
        resp.raise_for_status()
        return Shipment.model_validate(resp.json())

    async def aclose(self) -> None:
        await self._client.aclose()


def _pick_one(items: list[InventoryItem], sku: str) -> InventoryItem:
    if not items:
        raise LookupError(f"未找到 SKU={sku} 的库存记录")
    return max(items, key=lambda i: i.available)


class InMemoryWmsClient:
    def __init__(self) -> None:
        self._inventory: list[InventoryItem] = [InventoryItem(**r) for r in INVENTORY_ROWS]
        self._orders: dict[str, Order] = {r["order_id"]: Order(**r) for r in ORDER_ROWS}
        self._shipments: dict[str, Shipment] = {r["tracking_no"]: Shipment(**r) for r in SHIPMENT_ROWS}
        self._seq = 100

    async def get_inventory(self, sku: str, warehouse: str | None = None) -> InventoryItem:
        wh = normalize_warehouse(warehouse)
        items = [i for i in self._inventory if i.sku == sku and (wh is None or i.warehouse == wh)]
        return _pick_one(items, sku)

    async def get_order(self, order_id: str) -> Order:
        try:
            return self._orders[order_id]
        except KeyError as e:
            raise LookupError(f"未找到订单 {order_id}") from e

    async def create_shipment(self, booking: ShipmentBooking) -> Shipment:
        if booking.order_id not in self._orders:
            raise LookupError(f"订单 {booking.order_id} 不存在，无法开运单")
        self._seq += 1
        shipment = Shipment(
            tracking_no=f"TRK-{self._seq}",
            order_id=booking.order_id,
            carrier=booking.carrier,
            status="booked",
            current_location="待揽收",
            eta=datetime.now(timezone.utc) + timedelta(days=2),
        )
        self._shipments[shipment.tracking_no] = shipment
        return shipment

    async def track_shipment(self, tracking_no: str) -> Shipment:
        try:
            return self._shipments[tracking_no]
        except KeyError as e:
            raise LookupError(f"未找到运单 {tracking_no}") from e
