"""Validation helpers for the local, non-executable text document store."""
from pathlib import PurePosixPath

MAX_TEXT_BYTES = 2 * 1024 * 1024


def validate_text_upload(filename: str | None, content_type: str | None, content: bytes) -> str:
    name = PurePosixPath((filename or "").replace("\\", "/")).name
    name = "".join(char for char in name if char.isprintable()).strip()
    if not name or len(name) > 180 or PurePosixPath(name).suffix.lower() != ".txt":
        raise ValueError("Only a named .txt file is supported")
    if content_type not in {None, "", "text/plain", "application/octet-stream"}:
        raise ValueError("Only plain-text uploads are supported")
    if not content or len(content) > MAX_TEXT_BYTES:
        raise ValueError("Text files must be between 1 byte and 2 MiB")
    if b"\x00" in content:
        raise ValueError("Text file contains binary data")
    try:
        content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ValueError("Text files must use UTF-8 encoding") from None
    return name
