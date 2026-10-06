"""WMS 客户端（内存假数据）单元测试。"""

import asyncio

from logistics_agent.wms_client import InMemoryWmsClient
from logistics_agent.models import ShipmentBooking


def test_inventory_picks_specific_warehouse():
    client = InMemoryWmsClient()
    item = asyncio.run(client.get_inventory("SKU-1001", "WH-SH"))
    assert item.warehouse == "WH-SH"
    assert item.available == 85


def test_inventory_without_warehouse_picks_max_available():
    client = InMemoryWmsClient()
    item = asyncio.run(client.get_inventory("SKU-1001"))
    assert item.warehouse == "WH-SH"
    assert item.available == 85


def test_inventory_missing_sku_raises():
    client = InMemoryWmsClient()
    try:
        asyncio.run(client.get_inventory("SKU-9999"))
    except LookupError:
        pass
    else:
        raise AssertionError("expected LookupError")


def test_get_order():
    client = InMemoryWmsClient()
    order = asyncio.run(client.get_order("ORD-1002"))
    assert order.status == "shipped"
    assert order.warehouse == "WH-SZ"
    # 已发货的订单应带运单号，Agent 才能自动调用 track_shipment 而非反问用户
    assert order.tracking_no == "TRK-8881"


def test_create_and_track_shipment():
    client = InMemoryWmsClient()
    booking = ShipmentBooking(order_id="ORD-1003", carrier="京东物流")
    shipment = asyncio.run(client.create_shipment(booking))
    assert shipment.status == "booked"
    tracked = asyncio.run(client.track_shipment(shipment.tracking_no))
    assert tracked.carrier == "京东物流"
