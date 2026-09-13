"""Check real HTTP, Swagger and browser behavior against isolated local servers."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def port():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


def request(url, method='GET', data=None):
    try:
        with urlopen(Request(url, method=method, data=data, headers={'Content-Type': 'application/json'}), timeout=3) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()


@contextmanager
def server(command, cwd, env, log, ready):
    with log.open('w') as output:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + 60
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f'Server exited; see {log}')
                try:
                    if request(ready)[0] == 200:
                        break
                except (URLError, TimeoutError):
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError(f'Server did not become ready; see {log}')
                time.sleep(0.1)
            yield
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports', type=Path, required=True)
    reports = parser.parse_args().reports.resolve()
    reports.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    api_port, ui_port = port(), port()
    while ui_port == api_port:
        ui_port = port()
    api, ui = f'http://127.0.0.1:{api_port}', f'http://127.0.0.1:{ui_port}'
    env = {**os.environ, 'DEBUG': 'false', 'DEMO_MODE': 'false',
           'DATABASE_URL': f'sqlite+aiosqlite:///{reports / "unused-smoke.db"}',
           'NEXT_TELEMETRY_DISABLED': '1', 'NEXT_PUBLIC_DEMO_MODE': '1'}
    with server([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
                 '--port', str(api_port)], root / 'backend', env, reports / 'api.log', api + '/docs'):
        status, docs = request(api + '/docs')
        if status != 200 or b'SwaggerUIBundle' not in docs:
            raise RuntimeError('Swagger UI is unavailable')
        (reports / 'swagger.html').write_bytes(docs)
        status, schema = request(api + '/openapi.json')
        if status != 200:
            raise RuntimeError('OpenAPI is unavailable')
        catalog = json.loads(schema)
        operation = catalog['paths']['/api/v1/internal/report-jobs/{report_id}/execute']['post']
        if not {'401', '403', '409', '503'} <= set(operation['responses']):
            raise RuntimeError('Internal job errors are missing from Swagger')
        (reports / 'openapi.json').write_bytes(schema)
        status, _ = request(api + '/api/v1/internal/report-jobs/1/execute', 'POST', b'{"report_id":"1"}')
        if status != 401:
            raise RuntimeError(f'Anonymous job execution returned {status}, expected 401')
        with server(['npm', 'run', 'start', '--', '--hostname', '127.0.0.1', '--port', str(ui_port)],
                    root / 'frontend', env, reports / 'frontend.log', ui + '/tests'):
            subprocess.run(['node', 'tests/e2e/pipeline.mjs'], cwd=root, check=True,
                           env={**env, 'AUDIT_BASE_URL': ui,
                                'AUDIT_ARTIFACTS': str(reports / 'browser')})
    (reports / 'http-summary.json').write_text(json.dumps({
        'swagger': 200, 'openapi': 200, 'anonymous_execution': 401,
        'browser': 'desktop and mobile passed',
    }, indent=2) + '\n')
    print('Real HTTP, Swagger and browser smoke checks passed', flush=True)


if __name__ == '__main__':
    main()
