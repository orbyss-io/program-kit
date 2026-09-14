"""Bounded diagnostic evidence shared by maintained and consumer compatibility recipes."""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from package_execution import redact

MAX_BYTES = 256 * 1024


def sanitize(text: str) -> str:
    references = [{'credentialEnvironment': key} for key, value in os.environ.items()
                  if len(value) >= 8 and re.search(r'(?i)(token|password|secret|api_key|credential)', key)]
    text = redact(text, references)
    text = re.sub(r'(?i)(authorization\s*[:=]\s*(?:bearer|basic)\s+)\S+', r'\1[REDACTED]', text)
    text = re.sub(r'(?i)((?:password|client_secret|access_token|refresh_token)\s*[=:]\s*)[^\s&<>]+',
                  r'\1[REDACTED]', text)
    return text


def preserve(source: Path, destination: Path) -> dict:
    """Keep a bounded sanitized view and provenance even for a failing/malformed result."""
    digest = hashlib.sha256()
    size = 0
    captured = bytearray()
    with source.open('rb') as stream:
        while chunk := stream.read(65536):
            digest.update(chunk)
            size += len(chunk)
            if len(captured) < MAX_BYTES:
                captured.extend(chunk[:MAX_BYTES - len(captured)])
    original = captured.decode('utf-8', errors='replace')
    safe = sanitize(original)
    destination.write_text(safe, encoding='utf-8', newline='\n')
    return {'rawSha256': digest.hexdigest(), 'rawBytes': size,
            'truncated': size > MAX_BYTES, 'redacted': safe != original}
