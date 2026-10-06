"""共享演示数据：后端服务与内存客户端复用，保证两种模式行为一致。"""

from __future__ import annotations

INVENTORY_ROWS: list[dict] = [
    {"sku": "SKU-1001", "description": "云南草莓(冷链)", "warehouse": "WH-SH", "on_hand": 120, "allocated": 35, "available": 85, "unit": "箱"},
    {"sku": "SKU-1001", "description": "云南草莓(冷链)", "warehouse": "WH-SZ", "on_hand": 60, "allocated": 10, "available": 50, "unit": "箱"},
    {"sku": "SKU-1002", "description": "矿泉水 500ml*24", "warehouse": "WH-SH", "on_hand": 900, "allocated": 400, "available": 500, "unit": "箱"},
    {"sku": "SKU-1002", "description": "矿泉水 500ml*24", "warehouse": "WH-SZ", "on_hand": 1500, "allocated": 600, "available": 900, "unit": "箱"},
    {"sku": "SKU-1003", "description": "医用冷藏疫苗", "warehouse": "WH-SH", "on_hand": 40, "allocated": 38, "available": 2, "unit": "支"},
]

ORDER_ROWS: list[dict] = [
    {"order_id": "ORD-1001", "customer": "华东零售-李", "status": "allocated", "warehouse": "WH-SH",
     "lines": [{"sku": "SKU-1001", "quantity": 10}], "tracking_no": None},
    {"order_id": "ORD-1002", "customer": "华南连锁-王", "status": "shipped", "warehouse": "WH-SZ",
     "lines": [{"sku": "SKU-1002", "quantity": 50}], "tracking_no": "TRK-8881"},
    {"order_id": "ORD-1003", "customer": "跨境电商-赵", "status": "created", "warehouse": "WH-SZ",
     "lines": [{"sku": "SKU-1002", "quantity": 30}, {"sku": "SKU-1001", "quantity": 5}], "tracking_no": None},
]

SHIPMENT_ROWS: list[dict] = [
    {"tracking_no": "TRK-8881", "order_id": "ORD-1002", "carrier": "顺丰速运",
     "status": "in_transit", "current_location": "深圳转运中心", "eta": None},
]
