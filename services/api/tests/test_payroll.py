import unittest
import csv
from datetime import date
from decimal import Decimal

from app.payroll import calculate_period_pay, payroll_csv


class CalendarProrationTests(unittest.TestCase):
    def band(self, effective, base, allowances=None, deductions=None):
        return {
            "effective_from": date.fromisoformat(effective),
            "base_monthly": Decimal(base),
            "allowances": allowances or {},
            "deductions": deductions or {},
        }

    def test_full_month_uses_configured_monthly_values(self):
        result = calculate_period_pay(
            date(2026, 1, 1), date(2026, 1, 31), date(2024, 1, 1),
            [self.band("2025-01-01", "100000", {"Housing": "10000"}, {"Loan": "5000"})],
        )
        self.assertEqual(result["base"], Decimal("100000.00"))
        self.assertEqual(result["allowance_total"], Decimal("10000.00"))
        self.assertEqual(result["deduction_total"], Decimal("5000.00"))
        self.assertEqual(result["net"], Decimal("105000.00"))
        self.assertEqual(result["proration_days"], 31)

    def test_mid_month_hire_is_prorated_by_calendar_days(self):
        result = calculate_period_pay(
            date(2026, 1, 1), date(2026, 1, 31), date(2026, 1, 16),
            [self.band("2026-01-16", "31000")],
        )
        self.assertEqual(result["base"], Decimal("16000.00"))
        self.assertEqual(result["proration_days"], 16)

    def test_mid_month_compensation_change_creates_two_segments(self):
        result = calculate_period_pay(
            date(2026, 1, 1), date(2026, 1, 31), date(2024, 1, 1),
            [self.band("2025-01-01", "31000"), self.band("2026-01-16", "62000")],
        )
        self.assertEqual(result["base"], Decimal("47000.00"))
        self.assertEqual([segment["days"] for segment in result["segments"]], [15, 16])

    def test_missing_compensation_for_initial_eligible_days_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "No effective compensation"):
            calculate_period_pay(
                date(2026, 1, 1), date(2026, 1, 31), date(2024, 1, 1),
                [self.band("2026-01-10", "31000")],
            )

    def test_payroll_csv_escapes_spreadsheet_formulas(self):
        document = payroll_csv([{"employee_no": "=2+2", "employee": "@SUM(A1:A2)", "net_pay": "-10"}])
        self.assertTrue(document.startswith("\ufeff"))
        rows = list(csv.reader(document.lstrip("\ufeff").splitlines()))
        self.assertEqual(rows[1][0], "'=2+2")
        self.assertEqual(rows[1][1], "'@SUM(A1:A2)")
        self.assertEqual(rows[1][7], "'-10")



if __name__ == "__main__":
    unittest.main()
