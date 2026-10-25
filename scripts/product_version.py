"""Program Kit release identity; independent technology versions have their own owners."""
import re

PATTERN = r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-preview\.(?:0|[1-9][0-9]*))?'


def parse(value):
    if not isinstance(value, str) or not re.fullmatch(PATTERN, value):
        raise ValueError('Program Kit version must be N.N.N or N.N.N-preview.N')
    core, _, preview = value.partition('-preview.')
    return (*map(int, core.split('.')), int(preview) if preview else None)


def is_preview(value):
    return parse(value)[3] is not None


def order(value):
    major, minor, patch, preview = parse(value)
    return major, minor, patch, preview is None, preview or 0
