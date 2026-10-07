import unittest
from decimal import Decimal

from app.pos import cash_variance, pos_cash_totals

class PosCashLedgerTests(unittest.TestCase):
    def test_only_cash_sales_increase_expected_drawer_amount(self):
        totals = pos_cash_totals("500", [
            {"amount": "120.50", "tender": "cash"},
            {"amount": "90", "tender": "external_reference"},
        ])
        self.assertEqual(totals["cash_sales"], Decimal("120.50"))
        self.assertEqual(totals["expected_closing_cash"], Decimal("620.50"))

    def test_close_variance_is_counted_cash_minus_expected_cash(self):
        self.assertEqual(cash_variance("619.25", "620.50"), Decimal("-1.25"))

    def test_negative_cash_and_malformed_entries_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            pos_cash_totals("-1", [])
        with self.assertRaisesRegex(ValueError, "invalid"):
            cash_variance("not money", "10")


if __name__ == "__main__":
    unittest.main()
