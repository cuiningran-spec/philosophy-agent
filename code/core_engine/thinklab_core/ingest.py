"""知识库灌库 CLI：python -m thinklab_core.ingest [--rebuild]"""

from __future__ import annotations

import argparse

from .logging_utils import get_logger
from .service import ThinkLabAgent

logger = get_logger("ingest")


def main() -> None:
    parser = argparse.ArgumentParser(description="ThinkLab 哲学知识库灌库")
    parser.add_argument("--rebuild", action="store_true", help="先删除旧向量再重新灌入")
    parser.add_argument("--query", type=str, default=None, help="灌库后做一次检索测试")
    args = parser.parse_args()

    agent = ThinkLabAgent()
    result = agent.ingest(rebuild=args.rebuild)
    logger.info("灌库完成：%s", result)

    if args.query:
        logger.info("检索测试：query=%s", args.query)
        for index, item in enumerate(agent.search(args.query), start=1):
            logger.info("[%s] %s（%s） score=%s", index, item.title, item.school, item.score)


if __name__ == "__main__":
    main()
