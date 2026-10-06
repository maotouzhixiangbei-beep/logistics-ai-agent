"""命令行交互入口。"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from .agent import AgentDeps, get_agent
from .wms_client import HttpWmsClient, InMemoryWmsClient


def _check_api_key() -> str | None:
    model = os.getenv("LOGISTICS_AGENT_MODEL", "deepseek:deepseek-chat")
    model_lower = model.lower()
    if model_lower.startswith("deepseek"):
        if not os.getenv("DEEPSEEK_API_KEY"):
            return (
                "[错误] 未检测到 DEEPSEEK_API_KEY 环境变量。\n"
                "  请在当前 PowerShell 中执行（把 key 填到你的 .env 文件里后，推荐方案：复制 .env.example 为 .env 并填值，然后安装 python-dotenv）：\n"
                "    临时方案：$env:DEEPSEEK_API_KEY = \"sk-xxxx\"\n"
                "    CMD:        set DEEPSEEK_API_KEY=sk-xxxx\n"
                "    Bash:       export DEEPSEEK_API_KEY=sk-xxxx\n"
                "或切换到其他模型（例如 OpenAI），参考 .env.example。"
            )
    elif model_lower.startswith("openai"):
        if not os.getenv("OPENAI_API_KEY"):
            return (
                "[错误] 未检测到 OPENAI_API_KEY 环境变量。\n"
                "  PowerShell: $env:OPENAI_API_KEY = \"sk-xxxx\"\n"
                "  CMD:        set OPENAI_API_KEY=sk-xxxx\n"
                "  Bash:       export OPENAI_API_KEY=sk-xxxx"
            )
    return None


def build_deps() -> AgentDeps:
    base_url = os.getenv("WMS_BASE_URL")
    if base_url:
        print(f"[backend] 对接业务系统: {base_url}")
        return AgentDeps(wms=HttpWmsClient(base_url))
    print("[backend] 未设置 WMS_BASE_URL，使用内存假数据")
    return AgentDeps(wms=InMemoryWmsClient())


async def main() -> None:
    err = _check_api_key()
    if err:
        print(err, file=sys.stderr)
        sys.exit(1)
    deps = build_deps()
    agent = get_agent()
    print("物流 AI 助手已就绪，输入问题即可（quit 退出）。")
    print("示例：SKU-1001 在上海仓还有多少可用库存？")
    print("      ORD-1002 现在什么状态？帮我查一下运输进度。")
    async with agent:
        while True:
            try:
                question = input("> ").strip()
            except EOFError:
                break
            if question.lower() in {"quit", "exit", "q"}:
                break
            if not question:
                continue
            result = await agent.run(question, deps=deps)
            print(result.output)
            print()
    if isinstance(deps.wms, HttpWmsClient):
        await deps.wms.aclose()


if __name__ == "__main__":
    asyncio.run(main())
