"""Pure budget ledger calculations used by the control-plane API."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

CENT = Decimal("0.01")


def money(value: Any, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{label} must be numeric") from None
    if not result.is_finite():
        raise ValueError(f"{label} must be finite")
    return result.quantize(CENT, rounding=ROUND_HALF_UP)


def budget_totals(limit_value: Any, spent_value: Any = 0) -> dict[str, Any]:
    limit = money(limit_value, "Budget limit")
    spent = money(spent_value, "Budget spend")
    if limit <= 0:
        raise ValueError("Budget limit must be greater than zero")
    if spent < 0:
        raise ValueError("Budget spend cannot be negative")
    remaining = limit - spent
    return {"limit": limit, "spent": spent, "remaining": remaining, "over_budget": remaining < 0}


def add_budget_spend(limit_value: Any, spent_value: Any, amount_value: Any) -> dict[str, Any]:
    amount = money(amount_value, "Spend amount")
    if amount <= 0:
        raise ValueError("Spend amount must be greater than zero")
    totals = budget_totals(limit_value, spent_value)
    return budget_totals(totals["limit"], totals["spent"] + amount)
