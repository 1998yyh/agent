"""日志配置"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_dir: str = "./storage/logs",
    level: str = "INFO",
) -> logging.Logger:
    """设置日志

    参数:
        log_dir: 日志目录
        level: 日志级别

    返回:
        配置好的 logger 实例
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 创建 logger
    logger = logging.getLogger("devagent")
    logger.setLevel(getattr(logging, level.upper()))

    # 格式化
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（轮转）
    file_handler = RotatingFileHandler(
        log_path / "devagent.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 全局 logger
logger = setup_logging()
