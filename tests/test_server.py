"""后端服务接口测试：通过 ASGI 传输层做 HTTP 往返，不启动真实端口。"""

from fastapi.testclient import TestClient

from server.wms_api import app

client = TestClient(app)


def test_inventory_endpoint():
    r = client.get("/inventory/SKU-1001", params={"warehouse": "WH-SH"})
    assert r.status_code == 200
    data = r.json()
    assert data["warehouse"] == "WH-SH"
    assert data["available"] == 85


def test_order_endpoint():
    r = client.get("/orders/ORD-1002")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "shipped"
    assert data["tracking_no"] == "TRK-8881"


def test_create_and_track_shipment_endpoint():
    r = client.post("/shipments", json={"order_id": "ORD-1003", "carrier": "京东物流"})
    assert r.status_code == 201
    tracking_no = r.json()["tracking_no"]
    r2 = client.get(f"/shipments/{tracking_no}")
    assert r2.status_code == 200
    assert r2.json()["carrier"] == "京东物流"


def test_missing_order_returns_404():
    r = client.get("/orders/ORD-9999")
    assert r.status_code == 404
