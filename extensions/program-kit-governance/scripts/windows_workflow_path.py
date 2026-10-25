"""Prepare a Windows workflow PATH without changing persistent settings or tools.

This file also runs installed lifecycle commands as a source-only launcher for
consumers whose released runtime predates automatic Windows PATH preparation.
"""
from __future__ import annotations

import os
import errno
from pathlib import Path
import stat
import subprocess
import sys
import time
import uuid

CMD_PATH_LIMIT = 8191


def native_directory(path):
    """Shells require drive/UNC syntax; extended prefixes are for filesystem I/O."""
    value = str(path)
    if os.name == 'nt' and value.startswith('\\\\?\\'):
        value = '\\\\' + value[8:] if value.startswith('\\\\?\\UNC\\') else value[4:]
    return Path(value)


def file_snapshot(path):
    """Absence is distinct from an unreadable existing destination."""
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def replace_unchanged(temporary, target, previous):
    """Retry only an observed short Windows block without changing permissions."""
    for attempt in range(5):
        try:
            os.replace(temporary, target)
            return
        except PermissionError as error:
            if os.name != 'nt' or getattr(error, 'winerror', None) not in (5, 32, 33) or attempt == 4:
                raise
            time.sleep(.02 * (attempt + 1))
            try:
                unchanged = file_snapshot(target) == previous
            except OSError:
                unchanged = False
            if not unchanged:
                error.add_note('Destination changed or became unreadable while replacement was blocked; no retry.')
                raise


def write_bytes(path, content):
    """Replace a complete owned output using an exclusive same-directory sibling."""
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = file_snapshot(path)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        replace_unchanged(temporary, path, previous)
    finally:
        temporary.unlink(missing_ok=True)


class WindowsPathError(ValueError):
    pass


def path_length(value: str) -> int:
    return len(value.encode('utf-16-le', errors='surrogatepass')) // 2


def canonical_python(executable: str) -> str:
    """Resolve a Windows app-execution alias without loading project code."""
    if os.name != 'nt':
        return executable
    if os.path.normcase(os.path.abspath(executable)) == os.path.normcase(os.path.abspath(sys.executable)):
        return executable  # The running interpreter has already resolved this identity.
    try:
        result = subprocess.run([executable, '-I', '-c', 'import sys; print(sys.executable)'],
                                capture_output=True, text=True, encoding='utf-8', timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        raise WindowsPathError('WORKFLOW_RUNTIME_PREFLIGHT: the discovered Python launcher '
                               f'could not identify its interpreter: {error}; no worker was dispatched.') from error
    actual = result.stdout.strip()
    if result.returncode or not actual or not Path(actual).is_absolute() or not Path(actual).is_file():
        raise WindowsPathError('WORKFLOW_RUNTIME_PREFLIGHT: the discovered Python launcher '
                               'could not identify its interpreter; no worker was dispatched.')
    return actual


def short_directory(directory: str) -> str:
    """Use an existing NTFS short name only when it identifies the same directory."""
    import ctypes
    from ctypes import wintypes
    get_short = ctypes.WinDLL('kernel32', use_last_error=True).GetShortPathNameW
    get_short.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    get_short.restype = wintypes.DWORD
    size = get_short(directory, None, 0)
    if not size:
        return directory
    buffer = ctypes.create_unicode_buffer(size)
    written = get_short(directory, buffer, size)
    if not written or written >= size:
        return directory
    result = buffer.value
    try:
        if os.path.samefile(directory, result):
            return result
    except OSError:
        pass
    return directory


def prepare_path(inherited: str, python: str, *, limit: int = CMD_PATH_LIMIT) -> str:
    """Keep every usable directory in order, with the selected Python first.

    Only duplicate and missing directories are removed. Unreadable directories
    are retained. If necessary, existing short names reduce spelling length;
    useful tool directories are never silently truncated to fit CMD.
    """
    python_directory = str(Path(python).parent)
    if os.name != 'nt':
        return python_directory + os.pathsep + inherited
    directories, seen = [], set()
    for entry in [python_directory, *inherited.split(os.pathsep)]:
        entry = os.path.expandvars(entry.strip().strip('"'))
        if not entry:
            continue
        entry = os.path.abspath(entry)
        identity = os.path.normcase(os.path.normpath(entry))
        if identity in seen:
            continue
        try:
            if not stat.S_ISDIR(os.stat(entry).st_mode):
                continue
        except (FileNotFoundError, NotADirectoryError):
            continue
        except OSError as error:
            if error.errno == errno.ENAMETOOLONG or getattr(error, 'winerror', None) in {123, 206}:
                continue  # Invalid directory spelling cannot provide a native tool.
            pass  # Do not equate an access error with a missing tool directory.
        seen.add(identity)
        directories.append(entry)
    compact = os.pathsep.join(directories)
    if path_length(compact) > limit:
        # Keep Python's canonical spelling so interpreter identity remains bound
        # to the generated runtime record. Other aliases retain directory identity.
        compact = os.pathsep.join([directories[0], *map(short_directory, directories[1:])])
    if path_length(compact) > limit:
        raise WindowsPathError(
            'WORKFLOW_SHELL_PREFLIGHT: usable workflow tool directories still exceed '
            f'the Windows shell capacity ({path_length(compact)} characters, limit {limit}) '
            'after automatic PATH preparation. No tool directories were truncated, '
            'worker dispatched, or workflow history changed.')
    return compact


def main() -> int:
    print('The workflow launcher is retired. Use the installed product-intake skill and ordinary native Spec Kit phases; saved historical runs remain unchanged.', file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
