"""Deterministic report aggregation over already-authorized workspace records."""
from collections import Counter
from typing import Any, Iterable

REPORT_SOURCES = frozenset({"orders", "returns", "pos_sessions", "projects", "timesheets", "service_tickets", "field_jobs"})
REPORT_GROUPS = frozenset({"status", "branch"})


def aggregate_report(rows: Iterable[dict[str, Any]], group_by: str, status_filter: str = "") -> dict[str, Any]:
    if group_by not in REPORT_GROUPS:
        raise ValueError("Report grouping must be status or branch")
    selected = [row for row in rows if not status_filter or str(row.get("status", "")).lower() == status_filter.lower()]
    counts = Counter(str(row.get("status") or "unknown") if group_by == "status" else str(row.get("branch_id") or "unassigned") for row in selected)
    return {"record_count": len(selected), "group_by": group_by, "groups": dict(sorted(counts.items()))}
