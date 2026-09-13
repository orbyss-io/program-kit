"""Shared accepted-decision status parser."""
import re


def has_decision_status(text: str, status: str) -> bool:
    pattern = (
        r"^(?:[-*]\s+)?(?:Status:|\*\*Status\*\*:|\*\*Status:\*\*)\s*"
        + re.escape(status)
        + r"\s*$"
    )
    return re.search(pattern, text, re.MULTILINE | re.IGNORECASE) is not None
