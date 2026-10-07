"""Pure POS session cash expectations for the local register ledger."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable


def pos_cash_totals(opening_cash: Any, sales: Iterable[dict[str, Any]]) -> dict[str, Decimal]:
    cent = Decimal("0.01")
    try:
        opening = Decimal(str(opening_cash)).quantize(cent, rounding=ROUND_HALF_UP)
        cash_sales = Decimal("0")
        for sale in sales:
            amount = Decimal(str(sale["amount"]))
            if not amount.is_finite() or amount <= 0 or sale.get("tender") not in {"cash", "external_reference"}:
                raise ValueError("POS session cash totals are invalid")
            if sale["tender"] == "cash":
                cash_sales += amount
    except (InvalidOperation, ValueError, TypeError, KeyError):
        raise ValueError("POS session cash totals are invalid") from None
    if not opening.is_finite() or opening < 0 or not cash_sales.is_finite() or cash_sales < 0:
        raise ValueError("POS session cash totals are invalid")
    cash_sales = cash_sales.quantize(cent, rounding=ROUND_HALF_UP)
    return {"opening_cash": opening, "cash_sales": cash_sales, "expected_closing_cash": opening + cash_sales}


def cash_variance(closing_cash: Any, expected_cash: Any) -> Decimal:
    try:
        closing = Decimal(str(closing_cash))
        expected = Decimal(str(expected_cash))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("POS closing cash is invalid") from None
    if not closing.is_finite() or closing < 0 or not expected.is_finite():
        raise ValueError("POS closing cash is invalid")
    return (closing.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) - expected.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
