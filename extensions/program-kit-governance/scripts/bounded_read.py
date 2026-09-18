"""Read one repository document or JSON pointer in bounded, lossless pages."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

PAGE_BYTES = 6000


def read_page(root: Path, relative: str, page: int = 1, pointer: str | None = None) -> dict:
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Read path must be an existing file inside the repository.')
    data = path.read_bytes()
    text = data.decode('utf-8-sig')
    if pointer is not None:
        value = json.loads(text)
        if pointer and not pointer.startswith('/'):
            raise ValueError('JSON pointer must be empty or start with /.')
        for token in pointer.split('/')[1:] if pointer else []:
            key = token.replace('~1', '/').replace('~0', '~')
            if isinstance(value, list):
                if not key.isdecimal() or (key != '0' and key.startswith('0')):
                    raise ValueError('JSON array pointer requires a nonnegative canonical index.')
                value = value[int(key)]
            else:
                value = value[key]
        text = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    encoded = text.encode('utf-8')
    chunks, start = [], 0
    while start < len(encoded):
        end = min(start + PAGE_BYTES, len(encoded))
        while end < len(encoded) and encoded[end] & 0xC0 == 0x80:
            end -= 1
        chunks.append(encoded[start:end].decode('utf-8'))
        start = end
    chunks = chunks or ['']
    pages = len(chunks)
    if not 1 <= page <= pages:
        raise ValueError(f'Page must be between 1 and {pages}.')
    return {'path': path.relative_to(root).as_posix(), 'sha256': hashlib.sha256(data).hexdigest(),
            'pointer': pointer, 'page': page, 'pages': pages,
            'text': chunks[page - 1], 'next_page': page + 1 if page < pages else None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', required=True)
    parser.add_argument('--pointer')
    parser.add_argument('--page', type=int, default=1)
    args = parser.parse_args()
    try:
        result = read_page(Path.cwd(), args.path, args.page, args.pointer)
    except (OSError, UnicodeError, ValueError, KeyError, IndexError, TypeError) as error:
        print(f'Bounded read failed: {error}', file=sys.stderr)
        return 2
    print(f"{result['path']} sha256={result['sha256']} pointer={result['pointer']!r} page {result['page']}/{result['pages']}")
    print(result['text'])
    print(f"Next page: {result['next_page']}" if result['next_page'] else 'End of selected content.')
    return 0


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    raise SystemExit(main())
