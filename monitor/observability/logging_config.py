"""Structured JSON logging — the deliberately simple substitute for full tracing.

Full OpenTelemetry tracing across ingestion -> scoring -> alerting was
scoped out (see docs/phase5_findings.md): it needs a collector and an
exporter backend, real infrastructure this project's "keep it simple"
mandate doesn't justify yet. One JSON object per log line, to stdout, is a
container-native default that's greppable and parseable without any of
that — a real, working substitute for now, not a placeholder.
"""

import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    """Formats each log record as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Render one log record as a single-line JSON object."""
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger to emit one JSON object per line to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
