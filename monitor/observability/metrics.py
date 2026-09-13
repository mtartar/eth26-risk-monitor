"""Prometheus metrics for the ingestion -> scoring -> alerting pipeline.

Exposed at /metrics on the dashboard app (monitor/dashboard/app.py), scraped
by the prometheus service in docker-compose.yml.
"""

from prometheus_client import Counter, Histogram

EVENTS_PROCESSED = Counter(
    "monitor_events_processed_total",
    "Normalized lending events processed",
    ["event_kind"],
)
REORGS_HANDLED = Counter(
    "monitor_reorgs_handled_total",
    "Reorg (undo) signals processed",
)
RISK_TRANSITIONS = Counter(
    "monitor_risk_transitions_total",
    "Risk-level transitions reported",
    ["from_level", "to_level"],
)
ALERTS_SENT = Counter(
    "monitor_alerts_sent_total",
    "Alerts delivered",
    ["status"],
)
SINK_RETRIES = Counter(
    "monitor_sink_retries_total",
    "Sink retry attempts after an ingestion error",
)
LLM_CALL_DURATION = Histogram(
    "monitor_llm_call_duration_seconds",
    "Wall-clock time for one real Anthropic API call",
    ["kind"],
)
