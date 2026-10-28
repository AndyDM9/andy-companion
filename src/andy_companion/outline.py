"""Optional local mask outline on a confirmed finder picture, never a search/motor decision.

ANDY_OUTLINE_URL names a separately operated loopback /segment service. Unset, invalid,
unavailable, ambiguous or unsupported: show the ordinary picture. No downloads, model startup,
logs or retained pictures. This client implements the small JSON interface, not a model server.
"""
from __future__ import annotations

import base64
import json
import math
import os
import re
import urllib.request
from urllib.parse import urlsplit

MAX_REPLY = 256 * 1024
MAX_PATH = 8192
MAX_POINTS = 512
SIDE = 1024
TIMEOUT_S = 0.8


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def endpoint(value: str) -> str | None:
    """Numeric loopback only; no credentials, proxy, DNS, query, fragment or supplied path."""
    if not isinstance(value, str):
        return None
    try:
        p = urlsplit(value)
        if (p.scheme != 'http' or p.hostname not in ('127.0.0.1', '::1') or p.username is not None
                or p.password is not None or p.path not in ('', '/') or p.query or p.fragment
                or p.port is None or not 1 <= p.port <= 65535):
            return None
        host = '[::1]' if p.hostname == '::1' else '127.0.0.1'
        return f'http://{host}:{p.port}/segment'
    except (TypeError, ValueError):
        return None


def _number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Unsupported mask geometry')
    return float(value)


def _contours(mask, width, height):
    """Decode only closed absolute M/L/Z polygons into bounded image points; never render SVG."""
    import cv2
    import numpy as np

    box, scale, path = mask['box'], mask['outline_scale'], mask['outline']
    if not isinstance(box, list) or len(box) != 4 or not isinstance(scale, list) or len(scale) != 2:
        raise ValueError('Unsupported mask geometry')
    left, top, right, bottom = map(_number, box)
    sx, sy = map(_number, scale)
    if not (0 <= left < right <= width and 0 <= top < bottom <= height and 0 < sx <= width and 0 < sy <= height):
        raise ValueError('Unsupported mask geometry')
    if (right - left) * (bottom - top) > width * height * 0.75:
        raise ValueError('Scene-sized mask')
    if not isinstance(path, str) or not 1 <= len(path) <= MAX_PATH:
        raise ValueError('Unsupported mask path')
    tokens = re.findall(r'[MLZ]|[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', path)
    if re.sub(r'[MLZ]|[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|\s+', '', path):
        raise ValueError('Unsupported mask path')
    contours, points, count, i = [], None, 0, 0
    while i < len(tokens):
        command = tokens[i]
        i += 1
        if command == 'Z':
            if points is None or len(points) < 3 or len(contours) >= 16:
                raise ValueError('Unclosed mask path')
            contour = np.array(points, dtype=np.float32)
            if cv2.contourArea(contour) < 4:
                raise ValueError('Empty mask')
            contours.append(contour)
            points = None
            continue
        if command not in ('M', 'L') or i + 1 >= len(tokens) or (command == 'M') != (points is None):
            raise ValueError('Unsupported mask path')
        x, y = float(tokens[i]), float(tokens[i + 1])
        i += 2
        count += 1
        if not (math.isfinite(x) and math.isfinite(y) and 0 <= x * sx <= right - left
                and 0 <= y * sy <= bottom - top) or count > MAX_POINTS:
            raise ValueError('Unsupported mask geometry')
        if points is None:
            points = []
        points.append((left + x * sx, top + y * sy))
    if points is not None or not contours:
        raise ValueError('Unclosed mask path')
    return contours


def draw(frame, what: str, point: tuple, *, url: str | None = None, opener=None):
    """Return an outlined copy, or the unchanged input. Caller supplies a confirmed close-up/point.

    The numeric point must fall in exactly one qualifying mask. Scores do not confirm the object;
    that remains the existing Nemotron closer-look check. A timeout is per network operation.
    """
    target = endpoint(url if url is not None else os.environ.get('ANDY_OUTLINE_URL', ''))
    if target is None:
        return frame
    try:
        import cv2
        import numpy as np

        if (not isinstance(frame, np.ndarray) or frame.dtype != np.uint8 or frame.ndim != 3
                or frame.shape[2] != 3 or min(frame.shape[:2]) < 2
                or not isinstance(what, str) or not 1 <= len(what.strip()) <= 60
                or len(point) != 2 or any(not 0 <= _number(p) <= 1 for p in point)):
            return frame
        h, w = frame.shape[:2]
        ratio = min(1, SIDE / max(h, w))
        small = cv2.resize(frame, (max(2, round(w * ratio)), max(2, round(h * ratio)))) if ratio < 1 else frame
        sh, sw = small.shape[:2]
        ok, encoded = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ok:
            return frame
        body = {'image': base64.b64encode(encoded).decode(), 'query': what, 'min_score': 0.5}
        req = urllib.request.Request(target, json.dumps(body).encode(), {'Content-Type': 'application/json'})
        open_ = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect()).open
        with open_(req, timeout=TIMEOUT_S) as response:
            if response.status != 200:
                return frame
            raw = response.read(MAX_REPLY + 1)
        if len(raw) > MAX_REPLY:
            return frame
        data = json.loads(raw)
        masks = data.get('masks') if isinstance(data, dict) else None
        if not isinstance(masks, list) or not 1 <= len(masks) <= 12:
            return frame
        matches = []
        for mask in masks:
            try:
                if not isinstance(mask, dict) or not 0.5 <= _number(mask.get('score')) <= 1:
                    continue
                contours = _contours(mask, sw, sh)
                anchor = (float(point[0]) * sw, float(point[1]) * sh)
                if any(cv2.pointPolygonTest(c, anchor, False) >= 0 for c in contours):
                    matches.append(contours)
            except (TypeError, ValueError, KeyError, OverflowError):
                continue
        if len(matches) != 1:
            return frame
        out = frame.copy()
        contours = [np.round(c * [w / sw, h / sh]).astype(np.int32) for c in matches[0]]
        line = max(2, round(w / 160))
        cv2.polylines(out, contours, True, (10, 14, 22), line + 4, cv2.LINE_AA)
        cv2.polylines(out, contours, True, (106, 211, 255), line, cv2.LINE_AA)
        return out
    except Exception:
        return frame  # optional visual help cannot prevent a confirmed result; never echo payloads
