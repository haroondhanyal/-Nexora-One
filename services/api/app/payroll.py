"""Pure calendar-day payroll math for effective-dated monthly components."""
from datetime import date, timedelta
import csv
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO
from typing import Any

CENT = Decimal("0.01")


def payroll_csv(rows: list[dict[str, Any]]) -> str:
    """Render payroll values safely for spreadsheet import and review."""
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(["Employee no", "Employee", "Period start", "Period end", "Base pay", "Allowances", "Deductions", "Net pay"])
    for row in rows:
        cells = [
            row.get("employee_no", ""), row.get("employee", ""), row.get("period_start", ""), row.get("period_end", ""),
            row.get("base_pay", ""), row.get("allowance_total", ""), row.get("deduction_total", ""), row.get("net_pay", ""),
        ]
        writer.writerow([spreadsheet_safe(value) for value in cells])
    return "\ufeff" + output.getvalue()


def spreadsheet_safe(value: Any) -> str:
    text = str(value if value is not None else "")
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text


def calculate_period_pay(period_start: date, period_end: date, hire_date: date, compensations: list[dict[str, Any]]) -> dict[str, Any]:
    """Accrue monthly base, allowance and deduction values for eligible days.

    Each compensation item must contain effective_from, base_monthly,
    allowances and deductions. This is a calendar-day prorator, not a
    jurisdictional or attendance-based payroll engine.
    """
    if period_end < period_start:
        raise ValueError("Payroll period end must not precede its start")
    eligible_start = max(period_start, hire_date)
    period_days = (period_end - period_start).days + 1
    rows = sorted(
        (row for row in compensations if row["effective_from"] <= period_end),
        key=lambda row: row["effective_from"],
    )
    current = next((row for row in reversed(rows) if row["effective_from"] <= eligible_start), None)
    bands = ([current] if current else []) + [row for row in rows if row["effective_from"] > eligible_start]
    if current is None:
        bands = [row for row in rows if row["effective_from"] >= eligible_start]

    cursor = eligible_start
    segments = []
    for band in bands:
        segment_start = max(cursor, band["effective_from"])
        if segment_start > period_end:
            continue
        next_start = next((row["effective_from"] for row in rows if row["effective_from"] > segment_start), None)
        segment_end = min(period_end, next_start - timedelta(days=1)) if next_start else period_end
        if segment_end < segment_start:
            continue
        days = (segment_end - segment_start).days + 1
        segments.append({"band": band, "start": segment_start, "end": segment_end, "days": days})
        cursor = segment_end + timedelta(days=1)

    if not segments or segments[0]["start"] != eligible_start:
        raise ValueError("No effective compensation covers the employee's eligible payroll days")

    base_unrounded = Decimal("0")
    allowance_unrounded: dict[str, Decimal] = {}
    deduction_unrounded: dict[str, Decimal] = {}
    serialized_segments = []
    for segment in segments:
        band = segment["band"]
        factor = Decimal(segment["days"]) / Decimal(period_days)
        base_unrounded += Decimal(str(band["base_monthly"])) * factor
        for name, amount in band["allowances"].items():
            allowance_unrounded[name] = allowance_unrounded.get(name, Decimal("0")) + Decimal(str(amount)) * factor
        for name, amount in band["deductions"].items():
            deduction_unrounded[name] = deduction_unrounded.get(name, Decimal("0")) + Decimal(str(amount)) * factor
        serialized_segments.append({
            "start": segment["start"].isoformat(),
            "end": segment["end"].isoformat(),
            "days": segment["days"],
            "effective_from": band["effective_from"].isoformat(),
        })

    base = base_unrounded.quantize(CENT, rounding=ROUND_HALF_UP)
    allowances = {name: amount.quantize(CENT, rounding=ROUND_HALF_UP) for name, amount in allowance_unrounded.items()}
    deductions = {name: amount.quantize(CENT, rounding=ROUND_HALF_UP) for name, amount in deduction_unrounded.items()}
    allowance_total = sum(allowances.values(), Decimal("0"))
    deduction_total = sum(deductions.values(), Decimal("0"))
    net = base + allowance_total - deduction_total
    if net < 0:
        raise ValueError("Configured deductions exceed gross pay")
    return {
        "base": base,
        "allowances": allowances,
        "deductions": deductions,
        "allowance_total": allowance_total,
        "deduction_total": deduction_total,
        "net": net,
        "proration_days": sum(segment["days"] for segment in segments),
        "period_days": period_days,
        "segments": serialized_segments,
    }
