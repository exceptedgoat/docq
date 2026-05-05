"""
启动入口

用法:
    python -m src.rag.main              # 终端交互模式
    python -m src.rag.main web          # Web 服务模式
"""
import os
import sys

# HuggingFace 镜像
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from .config import GeneralConfig
from .rag import GeneralTerminalRAG
from .web import run_web


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        run_web()
    else:
        try:
            config = GeneralConfig()
            rag = GeneralTerminalRAG(config)
            rag.run()
        except Exception as e:
            print(f"启动失败：{e}")


if __name__ == "__main__":
    main()
