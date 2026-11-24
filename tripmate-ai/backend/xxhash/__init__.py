"""Small deterministic fallback for xxHash APIs used by LangGraph/LangSmith.

The native xxhash wheel can be blocked by host application-control policies.
This module keeps startup and hash-based graph/task IDs working in pure Python.
"""

import hashlib


class xxh3_128:
    """Pure-Python subset of xxhash.xxh3_128."""

    def __init__(self, data: bytes | str | None = None) -> None:
        self._data = _to_bytes(data)

    def digest(self) -> bytes:
        return hashlib.blake2b(self._data, digest_size=16).digest()

    def intdigest(self) -> int:
        return int.from_bytes(self.digest(), "big")

    def hexdigest(self) -> str:
        return self.digest().hex()


def _to_bytes(data: bytes | str | None) -> bytes:
    if data is None:
        return b""
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode("utf-8")
    return bytes(data)


def xxh3_128_hexdigest(data: bytes | str) -> str:
    return xxh3_128(data).hexdigest()
