import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

LOG_DIR = "logs"
LOG_FILE = "execution.log"
WARNING_FILE = "safety_warnings.log"

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)


def get_logger(name: str, filename: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    ensure_log_dir()
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ"
        )
        ch.setFormatter(ch_formatter)
        logger.addHandler(ch)

        target_file = filename or LOG_FILE
        fh = logging.FileHandler(os.path.join(LOG_DIR, target_file))
        fh.setLevel(level)
        fh_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ"
        )
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)

    return logger

execution_logger = get_logger("execution", filename=LOG_FILE, level=logging.INFO)
safety_logger = get_logger("safety", filename=WARNING_FILE, level=logging.WARNING)


def log_execution(action: Dict[str, Any], result: Dict[str, Any]) -> None:
    msg = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "result": result
    }
    execution_logger.info(f"Execution result: {msg}")


def log_safety_warning(code: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    msg = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "code": code,
        "message": message,
        "context": context or {}
    }
    safety_logger.warning(f"Safety warning: {msg}")
