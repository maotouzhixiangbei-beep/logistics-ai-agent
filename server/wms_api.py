"""演示用 WMS/OMS/TMS 后端服务（FastAPI + 内存数据，启动时播种）。"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi import FastAPI, HTTPException  # noqa: E402

from logistics_agent.models import InventoryItem, Order, Shipment, ShipmentBooking  # noqa: E402
from logistics_agent.seed import INVENTORY_ROWS, ORDER_ROWS, SHIPMENT_ROWS  # noqa: E402
from logistics_agent.wms_client import normalize_warehouse  # noqa: E402

app = FastAPI(title="Logistics WMS/OMS/TMS (demo)")

_inventory: list[InventoryItem] = [InventoryItem(**r) for r in INVENTORY_ROWS]
_orders: dict[str, Order] = {r["order_id"]: Order(**r) for r in ORDER_ROWS}
_shipments: dict[str, Shipment] = {r["tracking_no"]: Shipment(**r) for r in SHIPMENT_ROWS}
_seq = 100


def _pick_one(items: list[InventoryItem], sku: str) -> InventoryItem:
    if not items:
        raise HTTPException(status_code=404, detail=f"SKU={sku} 无库存记录")
    return max(items, key=lambda i: i.available)


@app.get("/inventory/{sku}", response_model=InventoryItem)
def get_inventory(sku: str, warehouse: str | None = None) -> InventoryItem:
    wh = normalize_warehouse(warehouse)
    items = [i for i in _inventory if i.sku == sku and (wh is None or i.warehouse == wh)]
    return _pick_one(items, sku)


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str) -> Order:
    if order_id not in _orders:
        raise HTTPException(status_code=404, detail=f"订单 {order_id} 不存在")
    return _orders[order_id]


@app.post("/shipments", response_model=Shipment, status_code=201)
def create_shipment(booking: ShipmentBooking) -> Shipment:
    if booking.order_id not in _orders:
        raise HTTPException(status_code=404, detail=f"订单 {booking.order_id} 不存在")
    global _seq
    _seq += 1
    shipment = Shipment(
        tracking_no=f"TRK-{_seq}",
        order_id=booking.order_id,
        carrier=booking.carrier,
        status="booked",
        current_location="待揽收",
        eta=datetime.now(timezone.utc) + timedelta(days=2),
    )
    _shipments[shipment.tracking_no] = shipment
    return shipment


@app.get("/shipments/{tracking_no}", response_model=Shipment)
def track_shipment(tracking_no: str) -> Shipment:
    if tracking_no not in _shipments:
        raise HTTPException(status_code=404, detail=f"运单 {tracking_no} 不存在")
    return _shipments[tracking_no]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
