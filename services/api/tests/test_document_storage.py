import unittest

from app.document_storage import MAX_TEXT_BYTES, validate_text_upload


class DocumentValidationTests(unittest.TestCase):
    def test_accepts_plain_utf8_text_and_sanitizes_windows_path(self):
        name = validate_text_upload(r"C:\private\notes.txt", "text/plain", "hello ✓".encode())
        self.assertEqual(name, "notes.txt")

    def test_rejects_executable_types_binary_and_invalid_utf8(self):
        for args in [
            ("payload.exe", "text/plain", b"hello"),
            ("payload.txt", "text/html", b"<script>"),
            ("payload.txt", "text/plain", b"\x00binary"),
            ("payload.txt", "text/plain", b"\xff"),
        ]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                validate_text_upload(*args)

    def test_enforces_nonempty_two_mib_limit(self):
        with self.assertRaisesRegex(ValueError, "between 1 byte"):
            validate_text_upload("empty.txt", "text/plain", b"")
        with self.assertRaisesRegex(ValueError, "between 1 byte"):
            validate_text_upload("big.txt", "text/plain", b"x" * (MAX_TEXT_BYTES + 1))


if __name__ == "__main__":
    unittest.main()
