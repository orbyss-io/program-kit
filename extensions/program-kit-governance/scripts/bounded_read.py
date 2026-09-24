"""Read one repository document or JSON pointer in bounded, lossless pages."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

PAGE_BYTES = 9000


def source_content(root: Path, relative: str, pointer: str | None = None, keys: bool = False) -> dict:
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f'Read path {relative!r} must be an existing file inside the repository; do not read an output before it is authored.')
    data = path.read_bytes()
    text = data.decode('utf-8-sig')
    if pointer is not None or keys or path.suffix.lower() == '.json':
        value = json.loads(text)
        if pointer and not pointer.startswith('/'):
            raise ValueError('JSON pointer must be empty or start with /.')
        for token in pointer.split('/')[1:] if pointer else []:
            key = token.replace('~1', '/').replace('~0', '~')
            if isinstance(value, list):
                if not key.isdecimal() or (key != '0' and key.startswith('0')):
                    raise ValueError('JSON array pointer requires a nonnegative canonical index.')
                value = value[int(key)]
            elif isinstance(value, dict):
                if key not in value:
                    names = ', '.join(str(k) for k in list(value)[:20])
                    raise ValueError(f'Unknown JSON key {key!r}; available keys: {names}. Omit --pointer for the root; / means an empty key.')
                value = value[key]
            else:
                raise ValueError('Cannot descend into a scalar JSON value.')
        if keys:
            value = {'type': type(value).__name__, 'keys': list(value) if isinstance(value, dict) else None,
                     'length': len(value) if isinstance(value, (list, dict)) else None}
        text = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    return {'path': path.relative_to(root).as_posix(), 'sha256': hashlib.sha256(data).hexdigest(),
            'pointer': pointer, 'text': text}


def paginate(text: str, page: int) -> dict:
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
    return {'page': page, 'pages': pages, 'text': chunks[page - 1],
            'next_page': page + 1 if page < pages else None}


def read_page(root: Path, relative: str, page: int = 1, pointer: str | None = None, keys: bool = False) -> dict:
    source = source_content(root, relative, pointer, keys)
    return {**source, **paginate(source['text'], page)}


def read_bundle(root: Path, paths: list[str], page: int = 1) -> dict:
    sources = [source_content(root, path) for path in dict.fromkeys(paths)]
    text = '\n\n'.join(f"SOURCE {s['path']} sha256={s['sha256']}\n{s['text']}" for s in sources)
    return {'path': 'source bundle', 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'pointer': None, **paginate(text, page)}



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', required=True, action='append')
    parser.add_argument('--keys', action='store_true', help='Show JSON keys without reading all values.')
    parser.add_argument('--pointer')
    parser.add_argument('--page', type=int, default=1)
    args = parser.parse_args()
    try:
        if len(args.path) > 1 and (args.pointer is not None or args.keys):
            raise ValueError('Pointers/key discovery require exactly one --path.')
        result = (read_page(Path.cwd(), args.path[0], args.page, args.pointer, args.keys) if len(args.path) == 1
                  else read_bundle(Path.cwd(), args.path, args.page))
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
