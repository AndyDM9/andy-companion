"""Round 8, B49: wave, and Andy waves back with its antennas. A wave is motion beside a still face that keeps
changing direction; walking or a still room is not; the antennas' wave stays under 2 rad/s."""

import math

import numpy as np
import pytest

pytest.importorskip("cv2")

from andy_companion.body import wave  # noqa: E402

W, H = 1920, 1080


def picture(hand_x=None, face_shift=0):
    f = np.full((H, W, 3), 60, np.uint8)
    f[420 + face_shift:620 + face_shift, 880:1040] = 180                    # a face in the middle
    if hand_x is not None:
        f[380:520, int(hand_x) - 50:int(hand_x) + 50] = 240                  # a hand beside it, at shoulder height
    return f


def run(frames, face=(0.0, -0.05)):
    d = wave.WaveDetector()
    seen = False
    for i, f in enumerate(frames):
        seen = d.feed(f, face[0], face[1], i / wave.WATCH_HZ) or seen
    return seen


def test_a_hand_waving_beside_a_still_face_is_a_wave():
    xs = [1350 + 120 * math.sin(2 * math.pi * 1.5 * i / wave.WATCH_HZ) for i in range(24)]
    assert run([picture(x) for x in xs])


def test_a_still_room_a_hand_held_up_and_a_person_walking_are_not():
    assert not run([picture() for _ in range(24)])
    assert not run([picture(1350) for _ in range(24)])                       # held still: no wave
    xs = [1350 + 120 * math.sin(2 * math.pi * 1.5 * i / wave.WATCH_HZ) for i in range(24)]
    assert not run([picture(x, face_shift=(i % 2) * 40) for i, x in enumerate(xs)])   # the face moving too
    assert not run([picture(1100 + 30 * i) for i in range(24)])              # one sweep across, no turning back


def test_the_wave_back_is_gentle_and_ends():
    t = {"now": 0.0}
    back = wave.WaveBack(clock=lambda: t["now"])
    back.start()
    rest = (-0.17, 0.17)
    out, steps = [], np.arange(0, wave.WAVE_S + 0.2, 0.01)
    for s in steps:
        t["now"] = float(s)
        out.append(back.step(rest))
    left = [a for a, _ in out]
    speed = max(abs(b - a) / 0.01 for a, b in zip(left, left[1:], strict=False))
    assert speed < 2.0 and max(left) - min(left) > 0.3                       # a visible wave, under the antennas' limit
    assert out[-1] == rest and not back.active()


def test_the_watcher_waves_back_once_then_waits():
    calls = []

    class Face:
        detected, x, y = True, 0.0, -0.05

    xs = iter([1350 + 120 * math.sin(2 * math.pi * 1.5 * i / wave.WATCH_HZ) for i in range(200)])
    t = {"now": 0.0}
    w = wave.WaveWatcher.__new__(wave.WaveWatcher)
    w._get_frame, w._get_face, w._active, w._wave_back, w._clock = (
        lambda: picture(next(xs)), lambda: Face(), lambda: True, lambda: calls.append(1), lambda: t["now"])
    w.detector, w.last = wave.WaveDetector(), -1e9
    for i in range(60):
        t["now"] = i / wave.WATCH_HZ
        w.look_once()
    assert calls == [1]                                                       # once, then the cooldown
