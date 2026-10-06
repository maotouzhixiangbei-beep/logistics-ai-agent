# logistics-ai-agent

用 **Pydantic AI** 构建的物流供应链 AI 助手：大模型通过 **Function Calling** 调用
WMS/OMS/TMS 业务系统的 REST 接口，回答库存、订单、运输等运营问题。

> 这是一个用于展示「Agent 编排 + 业务系统对接」的最小可运行项目，可作为 AI 应用
> 工程师岗位（物流方向）的项目经历。

## 架构

```
                     ┌──────────────────────────────────────┐
  用户提问 ───────▶  │  Pydantic AI Agent (Function Calling) │
  （自然语言）        │   instructions: 物流运营助手             │
                     │   @agent.tool  × 4 个工具               │
                     └───────────────┬──────────────────────┘
                                     │ 结构化参数/返回（Pydantic 模型）
                                     ▼
                     ┌──────────────────────────────────────┐
                     │        WmsClient（统一接口/适配层）      │
                     │  HttpWmsClient  │  InMemoryWmsClient   │
                     └───────────────┬──────────────────────┘
                                     │ HTTP (REST)
                     ┌───────────────▼──────────────────────┐
                     │  server/wms_api.py (FastAPI + 数据播种) │
                     │   /inventory  │ /orders │ /shipments    │
                     │   WMS          │ OMS      │ TMS          │
                     └──────────────────────────────────────┘
```

Agent 的工具只依赖 `WmsClient` 抽象，不关心后端是演示服务还是真实 ERP——
替换成 ERPNext / Odoo 时只需在 `HttpWmsClient` 层做 URL/字段适配。

## 目录结构

```
logistics-ai-agent/
├── src/logistics_agent/
│   ├── agent.py        # Pydantic AI Agent + 4 个 Function Calling 工具
│   ├── models.py       # 领域模型（工具入参与结构化返回）
│   ├── wms_client.py   # 业务系统客户端（HTTP 实现 + 内存假数据实现）
│   ├── seed.py         # 共享种子数据
│   └── cli.py          # 命令行交互入口
├── server/
│   └── wms_api.py      # 演示用 WMS/OMS/TMS 后端（FastAPI）
├── tests/              # 无需 API key 的测试
└── pyproject.toml
```

## 快速开始

### 1. 安装

```bash
# 建议 Python 3.11+
pip install -e ".[dev]"
```

### 2. 配置模型（任选其一）

复制 `.env.example` 为 `.env` 并填入，或直接导出环境变量：

```bash
# 方式 A：DeepSeek（推荐，便宜、国内直连）
export LOGISTICS_AGENT_MODEL=deepseek:deepseek-chat
export DEEPSEEK_API_KEY=sk-xxxx

# 方式 B：OpenAI
export LOGISTICS_AGENT_MODEL=openai:gpt-4o-mini
export OPENAI_API_KEY=sk-xxxx
```

### 3A. 快速体验（不启动后端，用内存假数据）

```bash
python -m logistics_agent.cli
```

```text
> SKU-1001 在上海仓还有多少可用库存？
> ORD-1002 现在什么状态？帮我查运输进度。
```

### 3B. 完整对接（启动业务后端）

```bash
# 终端 1：启动 WMS/OMS/TMS 后端
python server/wms_api.py

# 终端 2：让 Agent 通过 HTTP 对接后端
export WMS_BASE_URL=http://127.0.0.1:8000
python -m logistics_agent.cli
```

后端接口：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/inventory/{sku}?warehouse=` | 查库存（WMS） |
| GET | `/orders/{order_id}` | 查订单（OMS） |
| POST | `/shipments` | 开运单（TMS） |
| GET | `/shipments/{tracking_no}` | 查运输状态（TMS） |

## 测试（无需 LLM API key）

测试用 `FunctionModel` / `TestModel` 替代真实模型，全程 `ALLOW_MODEL_REQUESTS=False`，
不会发起任何真实 LLM 请求：

```bash
pytest -q
```

覆盖了三层：

1. `test_wms_client.py` — 业务系统客户端逻辑
2. `test_agent.py` — Agent 是否正确调用工具、是否用上真实种子数据
3. `test_server.py` — 后端 REST 接口的 HTTP 往返

## 对应目标岗位（物流 AI 应用工程师）的映射

| JD 能力要求 | 本项目对应点 |
| --- | --- |
| RAG / Agent / Function Calling | `@agent.tool` 4 个工具 = Function Calling；`instructions` 约束行为；结构化入参/返回 |
| AI 应用快速接入、API 封装 | `WmsClient` 抽象 + 领域 Pydantic 模型，工具只依赖接口 |
| 业务系统对接（TMS/WMS/OMS） | `/inventory`(WMS)、`/orders`(OMS)、`/shipments`(TMS) 三类接口 |
| 轻量化部署与调试 | 单文件 FastAPI 后端 + `python -m logistics_agent.cli`，两分钟跑通 |
| 快速验证效果并迭代优化 | 测试先行、无密钥 CI 可验证、模型层可替换（DeepSeek/OpenAI 切换） |

## 技术栈

Python · Pydantic AI · FastAPI · httpx · Pydantic · pytest

## License

MIT