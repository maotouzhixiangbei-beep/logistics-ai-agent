import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
for p in (SRC, ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
