"""Follow the person when their face isn't visible: back turned, to the side, across the room.

Pollen's tracking follows faces only and recentres 2 s after losing one. While no face is seen,
this finds a *person* in the camera picture with YOLOX (OpenCV model zoo, Apache-2.0, pinned on
Hugging Face) about 1.4 times a second on 2 CPU threads (less often when nobody has been seen for a while),
and gives seek the direction to turn to.

Privacy, as with faces: frames are looked at and dropped; nothing is stored or sent anywhere.

    python -m andy_companion.body.person      one look: people in view and their directions
"""

from __future__ import annotations

import os
import math
import time
import threading
from typing import Any, Dict, Callable, List, Optional, Tuple

import numpy as np

MODEL = ("opencv/object_detection_yolox", "object_detection_yolox_2022nov.onnx", "78c368f74ce73ee28fc7a1be418a598c71b58b52")
INPUT = 640
ENABLED = os.environ.get("ANDY_PERSON_FOLLOW", "on").lower() != "off"
MIN_SCORE = float(os.environ.get("ANDY_PERSON_SCORE", "0.45"))
PERIOD_S = 0.7             # about 1.4 checks a second while following (each check is ~150 ms on 2 threads;
                           # 3 a second kept about one core busy: measured 2026-10-06). Face tracking and
                           # voice direction respond at once; this only fills in when the face is lost.
THREADS = int(os.environ.get("ANDY_PERSON_THREADS", "2"))
IDLE_PERIOD_S, IDLE_AFTER_S = 1.5, 30.0     # nobody seen for 30 s: every 1.5 s
AWAY_PERIOD_S, AWAY_AFTER_S = 3.0, 600.0    # nobody for 10 minutes: every 3 s
FRESH_S = 1.0                # a sighting stays current until the next look (PERIOD_S plus one check)
# Reachy Mini Lite camera at 1920x1080 (from its calibration, resized_K): fx 1116 px, cx 953.
DEFAULT_FX, DEFAULT_CX = 1116.0, 953.0

Box = Tuple[float, float, float, float, float]       # x1, y1, x2, y2, score (pixels)


def _anchors() -> Tuple[np.ndarray, np.ndarray]:
    grids, strides = [], []
    for stride in (8, 16, 32):
        size = INPUT // stride
        xv, yv = np.meshgrid(np.arange(size), np.arange(size))
        grid = np.stack((xv, yv), 2).reshape(1, -1, 2)
        grids.append(grid)
        strides.append(np.full((*grid.shape[:2], 1), stride))
    return np.concatenate(grids, 1), np.concatenate(strides, 1)


def letterbox(frame: np.ndarray) -> Tuple[np.ndarray, float]:
    """RGB, scaled to fit 640x640 and padded with 114, as OpenCV's YOLOX demo does."""
    import cv2

    h, w = frame.shape[:2]
    r = min(INPUT / h, INPUT / w)
    padded = np.full((INPUT, INPUT, 3), 114, np.float32)
    small = cv2.resize(frame, (int(w * r), int(h * r)), interpolation=cv2.INTER_AREA)   # shrink first: far cheaper
    padded[:int(h * r), :int(w * r)] = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    return np.transpose(padded, (2, 0, 1))[None], r




def decode(output: np.ndarray, r: float, grids: np.ndarray, strides: np.ndarray, cls: int = 0,
           min_score: Optional[float] = None) -> List[Box]:
    """Objects of one COCO class (0, people, by default) from YOLOX's raw output, in original-frame pixels."""
    import cv2

    min_score = MIN_SCORE if min_score is None else min_score
    dets = output[0].copy()
    dets[:, :2] = (dets[:, :2] + grids[0]) * strides[0]
    dets[:, 2:4] = np.exp(dets[:, 2:4]) * strides[0]
    scores = dets[:, 4] * dets[:, 5 + cls]                  # objectness x class
    keep = scores >= min_score
    if not keep.any():
        return []
    d, s = dets[keep], scores[keep]
    xyxy = np.stack([d[:, 0] - d[:, 2] / 2, d[:, 1] - d[:, 3] / 2, d[:, 0] + d[:, 2] / 2, d[:, 1] + d[:, 3] / 2], 1) / r
    idx = cv2.dnn.NMSBoxes([[float(x1), float(y1), float(x2 - x1), float(y2 - y1)] for x1, y1, x2, y2 in xyxy],
                           s.tolist(), min_score, 0.5)
    return [(*map(float, xyxy[i]), float(s[i])) for i in np.array(idx).reshape(-1)]


def bearing(box: Box, fx: float = DEFAULT_FX, cx: float = DEFAULT_CX) -> float:
    """Head-relative yaw toward the person's centre; positive turns left (Pollen's convention)."""
    return math.atan2(cx - (box[0] + box[2]) / 2, fx)


class PersonDetector:
    def __init__(self) -> None:
        import cv2
        from huggingface_hub import hf_hub_download

        # OpenCV uses every core by default: 9 of them at 5 checks a second, and slower than 2
        # (measured 2026-10-06). The desktop is shared, so a small fixed number.
        cv2.setNumThreads(THREADS)
        self._net = cv2.dnn.readNet(hf_hub_download(MODEL[0], MODEL[1], revision=MODEL[2]))
        self._grids, self._strides = _anchors()
        self._lock = threading.Lock()

    def detect(self, frame: np.ndarray, cls: int = 0, min_score: Optional[float] = None) -> List[Box]:
        blob, r = letterbox(frame)
        with self._lock:
            self._net.setInput(blob)
            out = self._net.forward(self._net.getUnconnectedOutLayersNames())[0]
        return decode(out, r, self._grids, self._strides, cls, min_score)


_shared: Dict[str, Any] = {"detector": None}
_shared_lock = threading.Lock()


def shared_detector() -> "PersonDetector":
    """One model in memory for the person watch and the phone watch."""
    with _shared_lock:
        if _shared["detector"] is None:
            _shared["detector"] = PersonDetector()
        return _shared["detector"]


def period(latest: Optional[Tuple[float, float]], now: float) -> float:
    """How long to wait between looks: often while following someone, rarely when nobody is around."""
    since = now - latest[1] if latest is not None else float("inf")
    return PERIOD_S if since < IDLE_AFTER_S else IDLE_PERIOD_S if since < AWAY_AFTER_S else AWAY_PERIOD_S


class PersonWatcher:
    """A background thread: while `active()`, look for a person and keep the latest direction."""

    def __init__(self, get_frame: Callable[[], Optional[np.ndarray]], active: Callable[[], bool],
                 intrinsics: Callable[[], Tuple[float, float]] = lambda: (DEFAULT_FX, DEFAULT_CX),
                 detector: Optional[PersonDetector] = None) -> None:
        self._get_frame, self._active, self._intrinsics = get_frame, active, intrinsics
        self._detector = detector
        self._latest: Optional[Tuple[float, float]] = None      # (yaw, seen at)
        self.top: Optional[float] = None                         # top of the person, as a fraction of the height
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, name="andy-person", daemon=True)
        self.thread.start()

    def latest(self, now: float, max_age: float = FRESH_S) -> Optional[float]:
        seen = self._latest
        return seen[0] if seen and now - seen[1] <= max_age else None

    def look_once(self, now: float) -> Optional[float]:
        frame = self._get_frame()
        if frame is None:
            return None
        if self._detector is None:
            self._detector = shared_detector()
        people = self._detector.detect(frame)
        if not people:
            return None
        fx, cx = self._intrinsics()
        previous = self._latest[0] if self._latest else None
        found = [(bearing(p, fx, cx), (p[2] - p[0]) * (p[3] - p[1]), p) for p in people]
        # The same person as before if there is one nearby; otherwise the biggest (nearest).
        chosen = min(found, key=lambda y: abs(y[0] - previous)) if previous is not None else max(found, key=lambda y: y[1])
        self._latest = (chosen[0], now)
        self.top = max(0.0, chosen[2][1]) / frame.shape[0]
        return chosen[0]

    def top_now(self, now: float, max_age: float = FRESH_S) -> Optional[float]:
        return self.top if self.latest(now, max_age) is not None else None

    def _run(self) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                if self._active():
                    self.look_once(time.monotonic())
            except Exception:
                time.sleep(1.0)                                   # never take the control loop down
            # Nobody for a while (they're out of the room): look once a second instead of five times.
            self._stop.wait(max(0.0, period(self._latest, time.monotonic()) - (time.monotonic() - started)))

    def stop(self) -> None:
        self._stop.set()


def main() -> int:
    from reachy_mini import ReachyMini

    with ReachyMini(connection_mode="localhost_only") as mini:
        frame = None
        for _ in range(20):
            frame = mini.media.get_frame()
            if frame is not None:
                break
            time.sleep(0.2)
        if frame is None:
            print("No camera frame.")
            return 1
        people = PersonDetector().detect(frame)
        print(f"People in view: {len(people)}")
        for p in people:
            print(f"  score {p[4]:.2f}, direction {math.degrees(bearing(p)):+.0f}° (positive = their left)")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
