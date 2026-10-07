import unittest
from decimal import Decimal

from app.budget import add_budget_spend, budget_totals

class BudgetLedgerTests(unittest.TestCase):
    def test_spend_updates_remaining_and_flags_over_budget(self):
        result = add_budget_spend("1000", "900", "150.25")
        self.assertEqual(result["spent"], Decimal("1050.25"))
        self.assertEqual(result["remaining"], Decimal("-50.25"))
        self.assertTrue(result["over_budget"])

    def test_budget_currency_values_are_rounded_to_cents(self):
        result = budget_totals("10.005", "2.004")
        self.assertEqual(result["limit"], Decimal("10.01"))
        self.assertEqual(result["spent"], Decimal("2.00"))
        self.assertEqual(result["remaining"], Decimal("8.01"))

    def test_nonpositive_spend_and_budget_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            add_budget_spend("100", "0", "0")
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            budget_totals("0", "0")



if __name__ == "__main__":
    unittest.main()
