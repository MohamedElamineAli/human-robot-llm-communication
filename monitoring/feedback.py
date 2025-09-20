import os
import json
from tempfile import NamedTemporaryFile
from datetime import datetime
from typing import Dict, Any, List


class FeedbackStore:
    def __init__(self, filepath: str = "./data/feedback_store.json") -> None:
        self.filepath = filepath
        self._ensure_exists()

    def read_all(self) -> List[Dict[str, Any]]:
        self._ensure_exists()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def append(
        self,
        message: str,
        severity: str = "info",
        context: Dict[str, Any] | None = None,
    ) -> None:
        feedbacks = self.read_all()
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": message,
            "severity": severity,
            "context": context or {},
        }
        feedbacks.append(entry)
        self._safe_write_all(feedbacks)

    def _ensure_exists(self) -> None:
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(os.path.abspath(self.filepath)), exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _safe_write_all(self, feedbacks: List[Dict[str, Any]]) -> None:
        dirpath = os.path.dirname(os.path.abspath(self.filepath)) or "."
        with NamedTemporaryFile("w", dir=dirpath, delete=False, encoding="utf-8") as tmp:
            json.dump(feedbacks, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp.name, self.filepath)
