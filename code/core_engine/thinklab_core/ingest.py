"""知识库灌库 CLI：python -m thinklab_core.ingest [--rebuild]"""

from __future__ import annotations

import argparse

from .service import ThinkLabAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="ThinkLab 哲学知识库灌库")
    parser.add_argument("--rebuild", action="store_true", help="先删除旧向量再重新灌入")
    parser.add_argument("--query", type=str, default=None, help="灌库后做一次检索测试")
    args = parser.parse_args()

    agent = ThinkLabAgent()
    result = agent.ingest(rebuild=args.rebuild)
    print(f"灌库完成：{result}")

    if args.query:
        for index, item in enumerate(agent.search(args.query), start=1):
            print(f"[{index}] {item.title}（{item.school}） score={item.score}")


if __name__ == "__main__":
    main()
