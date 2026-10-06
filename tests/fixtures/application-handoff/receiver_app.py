"""Small ordinary-tools fixture: two HTTP APIs in one process, no storage or identity services."""
import argparse
from dataclasses import dataclass, fields
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path


MIN_CAPACITY = 1
MAX_CAPACITY = 10


@dataclass
class Settings:
    capacity: int = 2

    def __post_init__(self):
        if type(self.capacity) is not int or not MIN_CAPACITY <= self.capacity <= MAX_CAPACITY:
            raise ValueError('capacity must be an integer between 1 and 10')


ROUTES = {'/admission': ('Admission', 'admit'), '/capacity': ('Capacity', 'capacity')}


def metadata():
    return {'schemaVersion': 1, 'owner': 'application', 'scope': 'shared-process', 'complete': True,
            'sources': {'src/receiver_app.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
            'settings': [{'path': 'capacity', 'type': 'integer', 'required': False, 'secret': False,
                          'default': fields(Settings)[0].default, 'constraints': {'minimum': MIN_CAPACITY, 'maximum': MAX_CAPACITY},
                          'binding': 'The --capacity startup argument; integer parsing precedes Settings validation.',
                          'precedence': ['explicit --capacity', 'Settings.capacity default'], 'reload': 'restart',
                          'description': 'Maximum positive units accepted by the stateless admission API.'}],
            'semanticConstraints': ['No other settings; no storage, identity discovery or startup side effects during export.']}


def contract(route):
    identity, operation = ROUTES[route]
    field = 'admitted' if route == '/admission' else 'capacity'
    result_schema = {'type': 'object', 'required': [field], 'additionalProperties': False,
                     'properties': {field: {'type': 'boolean'} if field == 'admitted' else
                                    {'type': 'integer', 'minimum': MIN_CAPACITY, 'maximum': MAX_CAPACITY}}}
    operation_contract = {'operationId': operation, 'responses': {
        '200': {'description': 'JSON result', 'content': {'application/json': {'schema': result_schema}}}}}
    if route == '/admission':
        operation_contract['parameters'] = [{'name': 'units', 'in': 'query', 'required': True,
                                              'schema': {'type': 'integer'}}]
        operation_contract['responses']['400'] = {'description': 'Missing or non-integer units',
            'content': {'application/json': {'schema': {'type': 'object', 'required': ['error'],
            'additionalProperties': False, 'properties': {'error': {'type': 'string'}}}}}}
    return {'openapi': '3.0.3', 'info': {'title': identity, 'version': '1.2.3'},
            'paths': {route: {'get': operation_contract}}}


def serve(settings, ready):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            from urllib.parse import urlsplit, parse_qs
            parsed = urlsplit(self.path)
            status = 200
            if parsed.path == '/capacity':
                result = {'capacity': settings.capacity}
            elif parsed.path == '/admission':
                try:
                    units = int(parse_qs(parsed.query)['units'][0])
                    result = {'admitted': 0 < units <= settings.capacity}
                except (KeyError, ValueError):
                    status, result = 400, {'error': 'units must be an integer'}
            else:
                status, result = 404, {'error': 'unknown route'}
            data = json.dumps(result).encode()
            self.send_response(status); self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
        def log_message(self, *_):
            pass
    with HTTPServer(('127.0.0.1', 0), Handler) as server:
        Path(ready).write_text(str(server.server_port),encoding='utf-8')
        server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['serve', 'metadata', 'contracts'])
    parser.add_argument('--capacity', type=int, default=fields(Settings)[0].default)
    parser.add_argument('--ready', default='artifacts/port.txt')
    args = parser.parse_args()
    if args.command == 'metadata':
        print(json.dumps(metadata()))
    elif args.command == 'contracts':
        print(json.dumps({identity: contract(route) for route, (identity, _) in ROUTES.items()}))
    else:
        serve(Settings(args.capacity), args.ready)
