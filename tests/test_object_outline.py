"""Invented pixels/mask replies only. No models, household pictures or robot connections."""
import base64
import copy
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np
import pytest

from andy_companion import outline


@pytest.fixture(autouse=True)
def disabled(monkeypatch):
    monkeypatch.delenv('ANDY_OUTLINE_URL', raising=False)


@pytest.fixture
def frame():
    return np.full((200, 320, 3), 40, dtype=np.uint8)


MASK = {'box': [80, 40, 240, 160], 'score': 0.91, 'outline_scale': [2, 2],
        'outline': 'M 0 0 L 80 0 L 70 50 L 40 60 L 10 50 Z'}


class Reply(io.BytesIO):
    status = 200


def response(masks=None, raw=None, status=200):
    r = Reply(raw if raw is not None else json.dumps({'masks': [copy.deepcopy(MASK)] if masks is None else masks}).encode())
    r.status = status
    return r


@pytest.mark.parametrize('url', ['', None, 1, 'https://127.0.0.1:1234', 'http://localhost:1234',
    'http://192.168.1.2:1234', 'http://example.invalid:1234', 'file:///tmp/example',
    'http://127.0.0.2:1234', 'http://127.0.0.1', 'http://127.0.0.1:0', 'http://127.0.0.1:65536',
    'http://127.0.0.1:bad', 'http://127.0.0.1:1234/segment', 'http://127.0.0.1:1234/?x=1',
    'http://127.0.0.1:1234/#fragment', 'http://user:secret@127.0.0.1:1234'])
def test_remote_or_ambiguous_endpoints_are_refused(url):
    assert outline.endpoint(url) is None


@pytest.mark.parametrize('url,expected', [('http://127.0.0.1:1234/', 'http://127.0.0.1:1234/segment'),
                                       ('http://[::1]:1234', 'http://[::1]:1234/segment')])
def test_numeric_loopback_is_canonical(url, expected):
    assert outline.endpoint(url) == expected


def test_disabled_does_not_call_service(frame):
    assert outline.draw(frame, 'mug', (.5, .5), opener=lambda *a, **k: pytest.fail('disabled')) is frame


def test_outline_is_mask_shaped_and_input_is_unchanged(frame, capsys):
    original = frame.copy()
    def open_(req, timeout):
        body = json.loads(req.data)
        assert set(body) == {'image', 'query', 'min_score'}
        assert body['query'] == 'mug' and body['min_score'] == .5 and timeout == outline.TIMEOUT_S
        assert cv2.imdecode(np.frombuffer(base64.b64decode(body['image']), np.uint8), 1).shape == frame.shape
        assert req.full_url == 'http://127.0.0.1:1234/segment'
        return response()
    out = outline.draw(frame, 'mug', (.5, .5), url='http://127.0.0.1:1234', opener=open_)
    assert np.array_equal(frame, original) and not np.array_equal(out, frame)
    assert tuple(out[160, 160]) == (106, 211, 255)  # the pointed end of the contour, not the box
    assert np.array_equal(out[159, 239], original[159, 239])  # box corner is not traced
    assert capsys.readouterr() == ('', '')


@pytest.mark.parametrize('change', [
    {'score': .49}, {'score': True}, {'score': float('nan')}, {'score': float('inf')},
    {'score': 10**400}, {'box': [0, 0, 320, 200]}, {'box': [80, 40, 400, 160]},
    {'box': [160, 40, 80, 160]}, {'box': []}, {'outline_scale': [0, 1]}, {'outline_scale': [1]},
    {'outline': '<script>invented-private-value</script>'}, {'outline': 'M 0 0 C 1 1 2 2 3 3 Z'},
    {'outline': 'M 0 0 L 80 0 L 70 50'}, {'outline': 'M 0 0 L 80 0 Z'},
    {'outline': 'M 0 0 L 100000 0 L 0 50 Z'}, {'outline': 'M 0 0 L 1e400 0 L 0 50 Z'},
    {'outline': 'M 0 0 L 1 0 L 0 1 Z'}, {'outline': 'M 0 0 L -1 0 L 0 50 Z'},
    {'outline': 'Z'}, {'outline': ' ' * (outline.MAX_PATH + 1)},
])
def test_invalid_masks_show_original_without_echo(frame, capsys, change):
    m = {**MASK, **change}
    out = outline.draw(frame, 'mug', (.5, .5), url='http://127.0.0.1:1234', opener=lambda *a, **k: response([m]))
    assert out is frame and capsys.readouterr() == ('', '')


@pytest.mark.parametrize('masks', [[], [MASK, MASK], [None], [MASK] * 13])
def test_missing_ambiguous_or_excessive_masks_show_original(frame, masks):
    assert outline.draw(frame, 'mug', (.5, .5), url='http://127.0.0.1:1234',
                        opener=lambda *a, **k: response(masks)) is frame


@pytest.mark.parametrize('point', [(.05, .05), (1, 1), (float('nan'), .5), (True, .5), (-1, .5), (.5,), None])
def test_no_outline_for_invalid_or_unmatched_anchor(frame, point):
    assert outline.draw(frame, 'mug', point, url='http://127.0.0.1:1234',
                        opener=lambda *a, **k: response()) is frame


@pytest.mark.parametrize('raw,status', [(b'{', 200), (b'[]', 200), (b'null', 200), (b'\xff', 200),
                                      (b'x' * (outline.MAX_REPLY + 1), 200), (b'{}', 202), (b'{}', 502)])
def test_bad_transport_or_reply_shows_original(frame, raw, status):
    assert outline.draw(frame, 'mug', (.5, .5), url='http://127.0.0.1:1234',
                        opener=lambda *a, **k: response(raw=raw, status=status)) is frame


def test_timeout_does_not_fail_or_echo(frame, capsys):
    def timeout(*a, **k):
        raise TimeoutError('invented-private-value')
    assert outline.draw(frame, 'mug', (.5, .5), url='http://127.0.0.1:1234', opener=timeout) is frame
    assert capsys.readouterr() == ('', '')


def test_large_input_sends_bounded_copy_and_maps_contour_back():
    original = np.zeros((1200, 1600, 3), np.uint8)
    def open_(req, **kwargs):
        body = json.loads(req.data)
        sent = cv2.imdecode(np.frombuffer(base64.b64decode(body['image']), np.uint8), 1)
        assert sent.shape[:2] == (768, 1024)
        return response([{'box': [256, 192, 768, 576], 'score': .9, 'outline_scale': [1, 1],
                          'outline': 'M 0 0 L 512 0 L 512 384 L 0 384 Z'}])
    out = outline.draw(original, 'mug', (.5, .5), url='http://127.0.0.1:1234', opener=open_)
    assert out.shape == original.shape and not original.any()
    assert tuple(out[300, 400]) == (106, 211, 255)


def test_real_loopback_http_ignores_proxy_and_refuses_redirects(frame, monkeypatch):
    seen = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            seen.append((self.path, set(body)))
            if len(seen) == 1:
                raw = json.dumps({'masks': [MASK]}).encode()
                self.send_response(200); self.send_header('Content-Length', str(len(raw))); self.end_headers()
                self.wfile.write(raw)
            else:
                self.send_response(302)
                self.send_header('Location', f'http://127.0.0.1:{self.server.server_port}/must-not-follow')
                self.end_headers()
        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    monkeypatch.setenv('http_proxy', 'http://127.0.0.1:1')
    monkeypatch.setenv('no_proxy', '')
    url = f'http://127.0.0.1:{server.server_port}'
    try:
        assert outline.draw(frame, 'mug', (.5, .5), url=url) is not frame
        assert outline.draw(frame, 'mug', (.5, .5), url=url) is frame
        assert seen == [('/segment', {'image', 'query', 'min_score'})] * 2
    finally:
        server.shutdown(); server.server_close(); thread.join()
