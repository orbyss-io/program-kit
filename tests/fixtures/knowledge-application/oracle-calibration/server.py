"""Deliberately small oracle calibration double, NOT a reference upgrade consumer.

Fault switches prove the independent HTTP oracle rejects plausible broken behavior.
This is test infrastructure, with no claim of Program Kit architecture or adoption.
"""
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

if os.environ.get('ASPNETCORE_ENVIRONMENT') != 'ProgramKitAcceptanceFixture':
    raise SystemExit('Disposable fixture environment required')
store = Path(os.environ['LENDING_FIXTURE_DATA']) / 'state.json'
store.parent.mkdir(parents=True, exist_ok=True)
mutant = sys.argv[1] if len(sys.argv) > 1 else ''


def empty():
    return dict(available=2, reservations={}, notificationAttempts=0,
                notificationsSent=0, pendingNotifications=0, operations={}, failNext=False)


state = json.loads(store.read_text()) if store.is_file() and mutant != 'lost-restart' else empty()


def save():
    temporary = store.with_suffix('.tmp')
    temporary.write_text(json.dumps(state), encoding='utf-8')
    temporary.replace(store)


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate')
        result[key] = value
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, value=None):
        content = json.dumps(value).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path == '/__acceptance/snapshot':
            return self.reply(200, {key: state[key] for key in ('available', 'reservations', 'notificationAttempts', 'notificationsSent', 'pendingNotifications')})
        prefix = '/api/v1/reservations/'
        if self.path.startswith(prefix) and self.path[len(prefix):] in state['reservations']:
            return self.reply(200, state['reservations'][self.path[len(prefix):]])
        self.reply(404)

    def do_POST(self):
        if self.path.startswith('/__acceptance/'):
            operation = self.path.rsplit('/', 1)[1]
            if operation == 'reset':
                state.clear()
                state.update(empty())
            elif operation == 'fail-next-notification':
                state['failNext'] = True
            elif operation == 'drain-notifications':
                state['notificationAttempts'] += state['pendingNotifications']
                state['notificationsSent'] += state['pendingNotifications'] * (2 if mutant == 'duplicate-retry' else 1)
                state['pendingNotifications'] = 0
            else:
                return self.reply(404)
            save()
            return self.reply(200)
        try:
            body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))), object_pairs_hook=unique)
            if not isinstance(body, dict):
                raise ValueError('object')
        except (ValueError, TypeError):
            return self.reply(400)
        is_reserve = self.path == '/api/v1/reservations'
        operation = 'reserve' if is_reserve else self.path.rsplit('/', 1)[1]
        expected = {'operationId', 'equipmentId', 'quantity'} if is_reserve else {'operationId', 'acknowledged'} if operation == 'confirm' else {'operationId'}
        if set(body) != expected or not isinstance(body.get('operationId'), str):
            return self.reply(400)
        if is_reserve and (type(body['quantity']) is not int or body['quantity'] <= 0):
            return self.reply(400)
        if operation == 'confirm' and body['acknowledged'] is not True:
            return self.reply(400)
        previous = state['operations'].get(body['operationId'])
        fingerprint = [self.path, body]
        if previous:
            if previous['input'] != fingerprint:
                return self.reply(409)
            if mutant == 'duplicate-reserve' and is_reserve:
                state['available'] -= body['quantity']
                save()
            return self.reply(200, previous['response'])
        if is_reserve:
            if body['equipmentId'] != 'camera' or body['quantity'] > state['available']:
                if mutant == 'denied-effect':
                    state['notificationAttempts'] += 1
                    save()
                return self.reply(409)
            identity = 'reservation-' + str(len(state['reservations']) + 1)
            state['available'] -= body['quantity']
            value = dict(reservationId=identity, operationId=body['operationId'], equipmentId=body['equipmentId'], quantity=body['quantity'], state='Reserved')
            state['reservations'][identity] = value
            status = 201
        else:
            identity = self.path.split('/')[-2]
            value = state['reservations'].get(identity)
            if value is None:
                return self.reply(404)
            if value['state'] != 'Reserved' and mutant != 'illegal-transition':
                return self.reply(409)
            if operation == 'cancel':
                value['state'] = 'Cancelled'
                state['available'] += value['quantity']
                status = 200
            elif operation == 'confirm':
                value['state'] = 'Confirmed'
                state['notificationAttempts'] += 1
                if state['failNext']:
                    state['failNext'] = False
                    state['pendingNotifications'] += 1
                    status = 202
                else:
                    state['notificationsSent'] += 1
                    status = 200
            else:
                return self.reply(404)
        # JSON copy represents the immutable original operation result.
        state['operations'][body['operationId']] = {'input': fingerprint, 'response': json.loads(json.dumps(value))}
        save()
        self.reply(status, value)


HTTPServer(('127.0.0.1', int(os.environ['LENDING_FIXTURE_PORT'])), Handler).serve_forever()
