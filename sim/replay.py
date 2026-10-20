"""One of Andy's searches in simulation, step by step, as a short film for people without a robot (PLAN B51).

    MUJOCO_GL=egl uv run --project sim python sim/replay.py            writes docs/images/sim-search.mp4 and .gif

Judges may judge on the text, images and video alone, and won't have a Reachy Mini. This shows the physical part of
"where did I leave my glasses?" without one: on the left, Pollen's simulated room with Andy on the table and an arrow
for where its eye points; on the right, what the eye sees. The search is Andy's own (andy_companion.finder, through
sim/finder_sim.py): the four looks of the sweep, each read as six zoomed tiles by NVIDIA Nemotron 3.5 Super VL on
Nebius Token Factory, the sightings merged into places, the closer look within reach with its strict question, and
the point, scored against where the duck really is. Captions say each step. Live model calls, rendered pictures.
"""

from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import numpy as np  # noqa: E402

import finder_sim as fs  # noqa: E402
from andy_companion import finder  # noqa: E402

FPS = 15
PANEL = (960, 540)
INK, SOFT, MARK, WARM = (255, 255, 255), (200, 210, 225), (90, 220, 160), (255, 170, 60)


def font(size: int, bold: bool = False):
    from PIL import ImageFont

    names = [HERE.parent / "src/andy_companion/pages/fonts" / f"atkinson-hyperlegible-{700 if bold else 400}.woff2",
             Path(f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf")]
    for n in names:
        try:
            return ImageFont.truetype(str(n), size)
        except OSError:
            continue
    return ImageFont.load_default()


class Film:
    def __init__(self, scene: fs.Scene):
        self.s, self.frames = scene, []
        self.rgba = scene.m.geom_rgba.copy()
        self.big, self.small = font(30, True), font(22)

    def room(self, yaw: float, pitch: float, colour=(1.0, 0.65, 0.15, 1.0), length: float = 0.9):
        """Pollen's room from a free camera, Andy visible, an arrow from its eye along (yaw, pitch)."""
        import mujoco

        m = self.s.m
        for g in range(m.ngeom):
            if m.geom_rgba[g, 3] == 0:
                m.geom_rgba[g, 3] = 1.0
        cam = mujoco.MjvCamera()
        cam.lookat[:], cam.distance, cam.azimuth, cam.elevation = [0.42, 0.0, 0.02], 1.45, 205, -32
        r = self.s.renderer
        r.update_scene(self.s.d, camera=cam)
        fwd = np.array([math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), -math.sin(pitch)])
        scn = r.scene
        g = scn.geoms[scn.ngeom]
        mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_ARROW, np.zeros(3), np.zeros(3), np.zeros(9),
                            np.array(colour, dtype=np.float32))
        mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_ARROW, 0.008, self.s.eye, self.s.eye + fwd * length)
        scn.ngeom += 1
        img = np.ascontiguousarray(r.render()[:, :, ::-1])
        m.geom_rgba[:] = self.rgba
        return img

    def add(self, room, eye, title: str, line: str, hold_s: float = 0.0, n: int = 1):
        import cv2
        from PIL import Image, ImageDraw

        left = cv2.resize(room, PANEL, interpolation=cv2.INTER_AREA)
        right = cv2.resize(eye, PANEL, interpolation=cv2.INTER_AREA)
        top = np.hstack([left, right])
        bar = Image.new("RGB", (PANEL[0] * 2, 110), (20, 28, 46))
        d = ImageDraw.Draw(bar)
        d.text((28, 16), title, font=self.big, fill=INK)
        d.text((28, 62), line, font=self.small, fill=SOFT)
        d.text((PANEL[0] * 2 - 330, 16), "Andy's own search, in simulation", font=self.small, fill=SOFT)
        d.text((PANEL[0] * 2 - 330, 62), "left: the room · right: Andy's eye", font=self.small, fill=SOFT)
        frame = np.vstack([top, np.array(bar)[:, :, ::-1]])
        for _ in range(max(n, int(hold_s * FPS))):
            self.frames.append(frame)

    def write(self, out_mp4: Path) -> None:
        import cv2

        h, w = self.frames[0].shape[:2]
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.mp4"
            vw = cv2.VideoWriter(str(raw), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (w, h))
            for f in self.frames:
                vw.write(f)
            vw.release()
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-crf", "26", "-movflags", "+faststart", str(out_mp4)], check=True)


def overlay(eye, boxes=(), spots=(), close=None, label=""):
    """Andy's view with its tiles' outlines, the sightings, the close-up's box, in the frame's own pixels."""
    import cv2

    img = eye.copy()
    for (x0, y0, w, h) in boxes:
        cv2.rectangle(img, (x0 + 3, y0 + 3), (x0 + w - 3, y0 + h - 3), (220, 220, 220), 2)
    for (x, y) in spots:
        cv2.circle(img, (int(x * img.shape[1]), int(y * img.shape[0])), 46, (60, 170, 255), 6)
    if close is not None:
        rows, cols = close
        cv2.rectangle(img, (cols.start, rows.start), (cols.stop, rows.stop), (90, 220, 160), 8)
    if label:
        cv2.putText(img, label, (40, 80), cv2.FONT_HERSHEY_DUPLEX, 2.0, (255, 255, 255), 4, cv2.LINE_AA)
    return img


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=8)          # the layout in docs/images/sim-search.*
    ap.add_argument("--duck-scale", type=float, default=0.5)
    ap.add_argument("--out", default=str(HERE.parent / "docs/images/sim-search.mp4"))
    args = ap.parse_args(argv)
    what = "rubber duck"
    scene = fs.Scene(args.seed, args.duck_scale)
    truth = scene.place(True)
    film = Film(scene)
    pitch = math.radians(finder.PITCH_DEG)
    poses = [(math.radians(d), pitch) for d in finder.SWEEP_DEG]

    film.add(film.room(0.0, pitch), scene.look(0.0, pitch), '"Andy, where\'s the rubber duck?"',
             "The same search Andy runs on the robot: look around, zoom in, look closer, point.", hold_s=2.2)
    frames, prev = [], (0.0, pitch)
    for i, (yaw, p) in enumerate(poses):
        for k in range(1, 9):                                         # the head turning, then still
            y = prev[0] + (yaw - prev[0]) * k / 8
            film.add(film.room(y, p), scene.look(y, p), f"1. Looking around: view {i + 1} of 4",
                     f"The head turns {abs(finder.SWEEP_DEG[i]):.0f}° {'left' if yaw > 0 else 'right'} and 15° down, "
                     "and waits until it is still before the picture.")
        frames.append(scene.look(yaw, p))
        film.add(film.room(yaw, p), frames[-1], f"1. Looking around: view {i + 1} of 4",
                 "Each picture is 1920 x 1080, never shrunk.", hold_s=0.8)
        prev = (yaw, p)

    with ThreadPoolExecutor(4) as pool:
        results = list(pool.map(lambda f: finder.read_view(f, what, finder.ask), frames))
    places = finder.merge_places(results, poses)
    boxes = [(x0, y0, w, h) for (x0, y0, w, h, _) in finder.tiles(frames[0])]
    for i, r in enumerate(results):
        spots = [(s["x"], s["y"]) for s in r.get("sightings", [])]
        said = f"seen: \"{r['sightings'][0]['where']}\"" if spots else "not seen here"
        film.add(film.room(*poses[i]), overlay(frames[i], boxes, spots), "2. Zooming in: six tiles per view, read at once",
                 f"View {i + 1}: NVIDIA Nemotron 3.5 Super VL on Nebius Token Factory, {said}.", hold_s=1.4)

    chosen, final_close = None, None
    for place in places[:finder.MAX_CLOSER]:
        aim = (finder.within(place["yaw"], finder.REACH_YAW_DEG), finder.within(place["pitch"], finder.REACH_PITCH_DEG))
        for k in range(1, 9):
            y = prev[0] + (aim[0] - prev[0]) * k / 8
            q = prev[1] + (aim[1] - prev[1]) * k / 8
            film.add(film.room(y, q), scene.look(y, q), "3. Looking closer",
                     "The head turns straight at the best sighting, as far as it can reach, and holds still.")
        prev = aim
        frame = scene.look(*aim)
        box = finder._close_box(frame, finder.CLOSE_UP, finder.where_in_view(place["yaw"], place["pitch"], *aim))
        checked = finder.look_closer(frame[box].copy(), what)
        film.add(film.room(*aim), overlay(frame, close=box), "3. Looking closer: a close-up from the sharp middle",
                 f"\"Is it clearly the {what}?\" Only a plain yes counts: \"{'yes' if checked.get('yes') else 'no'}\".",
                 hold_s=1.6)
        import cv2
        film.add(film.room(*aim), cv2.resize(frame[box], (frame.shape[1], frame.shape[0])),
                 "3. Looking closer", f"The close-up: {'yes, ' + checked.get('where', '') if checked.get('yes') else 'no: try the next sighting'}.",
                 hold_s=1.6)
        if checked.get("yes"):
            chosen = finder.confirmed_place(place, {"frame": frame, "box": box, "head": aim, "checked": checked})
            final_close = frame[box]
            break
    if chosen:
        err = fs.angle_between((chosen["yaw"], chosen["pitch"]), (truth["yaw"], truth["pitch"]))
        eye = scene.look(chosen["yaw"], chosen["pitch"])
        film.add(film.room(chosen["yaw"], chosen["pitch"], colour=(0.35, 0.86, 0.63, 1.0)), overlay(eye, spots=[(0.5, 0.5)]),
                 f"4. Pointing: \"I think I see your {what}, {chosen['where']}.\"",
                 f"{err:.1f}° from where the duck really is. The TV shows the close-up.", hold_s=3.0)
    else:
        film.add(film.room(*prev), scene.look(*prev), "4. Not confirmed up close", "Andy says it couldn't see it, never a guess.",
                 hold_s=2.5)
    out = Path(args.out)
    film.write(out)
    gif = out.with_suffix(".gif")
    subprocess.run([str(HERE.parent / "scripts/make_gif.sh"), str(out), str(gif), "0",
                    str(len(film.frames) / FPS), "800"], check=True)
    try:
        scene.renderer.close()
    except Exception:
        pass
    print(f"{out} and {gif}: {len(film.frames) / FPS:.0f} s; {'found' if chosen else 'not found'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
