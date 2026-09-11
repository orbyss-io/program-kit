from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


DEFAULT_PATTERNS = (
    re.compile(rb"(?i)(authorization\s*:\s*bearer\s+)[^\s\r\n]+"),
    re.compile(rb"(?i)(PROGRAM_KIT_NPM_TOKEN\s*[=:]\s*)[^\s\r\n]+"),
    re.compile(rb"(?i)(npm_[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9_]{20,})"),
)


@dataclass(frozen=True)
class RedactionSummary:
    original_sha256: str
    redaction_count: int
    ruleset: str


class StreamingRedactor:
    """Hash raw bytes and retain only a redacted stream, including across chunk boundaries."""

    def __init__(self, secrets: list[str], ruleset: str = "live-redaction-v2"):
        encoded = [value.encode("utf-8") for value in secrets if value]
        self._secrets = sorted(set(encoded), key=len, reverse=True)
        self._patterns = DEFAULT_PATTERNS
        self._tail = b""
        self._hash = hashlib.sha256()
        self._count = 0
        self._ruleset = ruleset
        self._overlap = max([512, *(len(value) + 16 for value in self._secrets)])

    def _redact(self, value: bytes) -> bytes:
        result = value
        for secret in self._secrets:
            occurrences = result.count(secret)
            if occurrences:
                result = result.replace(secret, b"[REDACTED]")
                self._count += occurrences
        for pattern in self._patterns:
            def replace(match: re.Match[bytes]) -> bytes:
                self._count += 1
                if match.lastindex and match.lastindex > 1:
                    return b"[REDACTED]"
                if match.lastindex == 1 and match.group(1).lower().startswith((b"authorization", b"program_kit")):
                    return match.group(1) + b"[REDACTED]"
                return b"[REDACTED]"

            result = pattern.sub(replace, result)
        return result

    def feed(self, chunk: bytes) -> bytes:
        self._hash.update(chunk)
        combined = self._tail + chunk
        if len(combined) <= self._overlap:
            self._tail = combined
            return b""
        boundary = len(combined) - self._overlap
        spans: list[tuple[int, int]] = []
        for secret in self._secrets:
            start = 0
            while True:
                index = combined.find(secret, start)
                if index < 0:
                    break
                spans.append((index, index + len(secret)))
                start = index + 1
        for pattern in self._patterns:
            spans.extend((match.start(), match.end()) for match in pattern.finditer(combined))
        crossing = [start for start, end in spans if start < boundary < end]
        if crossing:
            boundary = min(crossing)
        prefix, self._tail = combined[:boundary], combined[boundary:]
        return self._redact(prefix)

    def finish(self) -> tuple[bytes, RedactionSummary]:
        final = self._redact(self._tail)
        self._tail = b""
        return final, RedactionSummary(self._hash.hexdigest(), self._count, self._ruleset)
