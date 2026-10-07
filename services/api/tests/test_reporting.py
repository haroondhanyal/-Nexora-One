import unittest

from app.reporting import aggregate_report


class LocalReportingTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"status": "open", "branch_id": "branch-a"},
            {"status": "open", "branch_id": "branch-a"},
            {"status": "closed", "branch_id": "branch-b"},
            {"status": "open", "branch_id": ""},
        ]

    def test_counts_are_grouped_by_status(self):
        self.assertEqual(aggregate_report(self.rows, "status"), {
            "record_count": 4, "group_by": "status", "groups": {"closed": 1, "open": 3},
        })

    def test_optional_status_filter_limits_the_aggregate(self):
        self.assertEqual(aggregate_report(self.rows, "branch", "OPEN"), {
            "record_count": 3, "group_by": "branch", "groups": {"branch-a": 2, "unassigned": 1},
        })

    def test_invalid_grouping_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "status or branch"):
            aggregate_report(self.rows, "employee_salary")


if __name__ == "__main__":
    unittest.main()
