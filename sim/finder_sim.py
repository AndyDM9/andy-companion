"""Andy's finder in simulation (PLAN B48): the same search, on Pollen's Reachy Mini MuJoCo scene, many times.

    MUJOCO_GL=egl uv run --project sim python sim/finder_sim.py --trials 20            on this computer (GPU)
    cloud/sim-job.sh 20                                                              as Nebius Serverless Jobs

Each trial puts the scene's rubber duck, croissant and apple at random places on its table (in a few trials the duck
is put out of sight, behind the robot), then runs Andy's own search from andy_companion.finder: the four views of the
sweep (SWEEP_DEG, PITCH_DEG), each read as zoomed tiles by the eyes Andy uses (vision.eyes: Nemotron 3.5 Super VL on
Token Factory by default), the sightings merged into places (merge_places), and the closer look at the best ones
(within reach, the close-up cut where the thing should show, the strict yes/no), as on the robot. The camera is a
virtual one at the robot's eye camera, turned as the head would turn, with the field of view the finder assumes
(FX at 1080p), and the robot's own body hidden so it never sees the inside of its head. Scored against the scene's
truth: found and pointed within POINTED_DEG of the duck; said not seen when it wasn't there; the pointing error.

What it tests: the search's logic and geometry, and the vision model on rendered pictures (not a real room's: the
real rate comes from the robot's recorded tries). `--zoom off` runs the old way, one shrunk picture per view.
The scorecard keeps numbers, never pictures.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import numpy as np  # noqa: E402

from andy_companion import finder, vision  # noqa: E402
from andy_companion.measure import percentile, wilson  # noqa: E402

POINTED_DEG = 6.0
WIDTH, HEIGHT = 1920, 1080
FOVY_DEG = math.degrees(2 * math.atan(HEIGHT / 2 / finder.FX))     # the finder's own camera model
OBJECTS = ("duck", "croissant", "apple")
REST_Z = {"duck": 0.0, "croissant": 0.03, "apple": 0.03}             # where each rests on the table top (the scene's own)


SCENE_VERSION = "1.12.0rc1"          # the robot's own reachy-mini (robot/pyproject.toml)
CACHE = HERE / ".cache"


def scene_dir() -> Path:
    """Pollen's MJCF: ANDY_SIM_MJCF; else the robot environment's installed reachy_mini; else fetched once from PyPI
    (the wheel's descriptions only, into sim/.cache), so the simulation needs no robot and no robot environment."""
    if os.environ.get("ANDY_SIM_MJCF"):
        return Path(os.environ["ANDY_SIM_MJCF"])
    import glob

    found = glob.glob(str(HERE.parent / "robot/.venv/lib/python3*/site-packages/reachy_mini/descriptions/reachy_mini/mjcf"))
    if found:
        return Path(found[0])
    kept = CACHE / "reachy_mini/descriptions/reachy_mini/mjcf"
    if not (kept / "scenes" / "minimal.xml").is_file():
        fetch_scene(CACHE)
    return kept


def fetch_scene(into: Path, version: str = SCENE_VERSION) -> None:
    """Pollen's reachy-mini wheel from PyPI, its descriptions (meshes, textures, MJCF) kept, nothing else."""
    import io
    import urllib.request
    import zipfile

    with urllib.request.urlopen(f"https://pypi.org/pypi/reachy-mini/{version}/json", timeout=30) as r:
        meta = json.loads(r.read())
    wheel = next(u for u in meta["urls"] if u["filename"].endswith(".whl"))
    print(f"Fetching Pollen's Reachy Mini scene ({wheel['filename']}, {wheel['size'] / 1e6:.0f} MB) once…", flush=True)
    with urllib.request.urlopen(wheel["url"], timeout=300) as r:
        data = r.read()
    import hashlib
    if hashlib.sha256(data).hexdigest() != wheel["digests"]["sha256"]:
        raise SystemExit("The downloaded wheel doesn't match PyPI's checksum.")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if "/descriptions/" in name:
                z.extract(name, into)


def camera_quat(yaw: float, pitch: float):
    """MuJoCo's camera looks along its -z with y up. Yaw positive turns left (Pollen's convention), pitch positive
    looks down: the columns of the camera's frame in the world, as a quaternion."""
    import mujoco

    fwd = np.array([math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), -math.sin(pitch)])
    right = np.array([math.sin(yaw), -math.cos(yaw), 0.0])
    up = np.cross(right, fwd)
    rot = np.stack([right, up, -fwd], axis=1)
    q = np.zeros(4)
    mujoco.mju_mat2Quat(q, rot.flatten())
    return q


class Scene:
    def __init__(self, seed: int = 0, duck_scale: float = 1.0):
        import mujoco

        self.mj = mujoco
        spec = mujoco.MjSpec.from_file(str(scene_dir() / "scenes" / "minimal.xml"))
        for mesh in spec.meshes:                                       # a smaller duck: about a pair of glasses
            if "duck" in mesh.name.lower():
                mesh.scale = [s * duck_scale for s in mesh.scale]
        spec.visual.global_.offwidth, spec.visual.global_.offheight = WIDTH, HEIGHT
        spec.worldbody.add_camera(name="andy_eye", pos=[0.039, 0.0, 0.202], fovy=FOVY_DEG)
        self.m = spec.compile()
        self.d = mujoco.MjData(self.m)
        mujoco.mj_forward(self.m, self.d)
        self.cam = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_CAMERA, "andy_eye")
        self.eye = np.array(self.m.cam_pos[self.cam])
        robot_root = self.m.body_rootid[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, "xl_330")]
        for g in range(self.m.ngeom):                                  # the robot's own body, hidden
            if self.m.body_rootid[self.m.geom_bodyid[g]] == robot_root:
                self.m.geom_rgba[g, 3] = 0.0
        self.table = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, "table")
        self.joints = {o: self.m.jnt_qposadr[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, f"{o}_joint")]
                       for o in OBJECTS}
        self.renderer = mujoco.Renderer(self.m, HEIGHT, WIDTH)
        self.rng = random.Random(seed)

    def on_table(self, x: float, y: float) -> bool:
        geomid = np.zeros(1, dtype=np.int32)
        dist = self.mj.mj_ray(self.m, self.d, np.array([x, y, 0.5]), np.array([0.0, 0.0, -1.0]), None, 1, -1, geomid)
        return dist > 0 and self.m.geom_bodyid[geomid[0]] == self.table

    def place(self, present: bool) -> dict:
        """The three things at random places on the table, apart; the duck behind the robot when not `present`."""
        spots = []
        for o in OBJECTS:
            for _ in range(500):
                x, y = self.rng.uniform(0.28, 1.1), self.rng.uniform(-0.55, 0.55)
                far = all(math.hypot(x - a, y - b) > 0.18 for a, b in spots)
                if far and self.on_table(x, y) and abs(math.degrees(math.atan2(y, x))) <= 62:
                    break
            if o == "duck" and not present:
                x, y = -0.6, 0.0                                       # behind the robot: out of every view
            spots.append((x, y))
            a = self.joints[o]
            turn = self.rng.uniform(-math.pi, math.pi)
            self.d.qpos[a:a + 7] = [x, y, REST_Z[o], math.cos(turn / 2), 0, 0, math.sin(turn / 2)]
        self.mj.mj_forward(self.m, self.d)
        duck = self.mj.mj_name2id(self.m, self.mj.mjtObj.mjOBJ_BODY, "duck")
        centre = np.mean([self.d.geom_xpos[g] for g in range(self.m.ngeom) if self.m.geom_bodyid[g] == duck], axis=0)
        dx, dy, dz = centre - self.eye                                # the duck's own middle, as seen from the eye
        return {"yaw": math.atan2(dy, dx), "pitch": math.atan2(-dz, math.hypot(dx, dy))}

    def look(self, yaw: float, pitch: float):
        """What the robot's eye sees with the head at (yaw, pitch): a BGR frame like the camera's."""
        self.m.cam_quat[self.cam] = camera_quat(yaw, pitch)
        self.mj.mj_forward(self.m, self.d)
        self.renderer.update_scene(self.d, camera=self.cam)
        return np.ascontiguousarray(self.renderer.render()[:, :, ::-1])


def angle_between(a: tuple, b: tuple) -> float:
    def v(yaw, pitch):
        return np.array([math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), -math.sin(pitch)])
    return math.degrees(math.acos(max(-1.0, min(1.0, float(v(*a) @ v(*b))))))


def trial(scene: Scene, present: bool, what: str) -> dict:
    truth = scene.place(present)
    pitch = math.radians(finder.PITCH_DEG)
    poses = [(math.radians(deg), pitch) for deg in finder.SWEEP_DEG]
    frames = [scene.look(*p) for p in poses]
    started = time.monotonic()
    with ThreadPoolExecutor(len(frames)) as pool:
        results = list(pool.map(lambda f: finder.read_view(f, what, finder.ask), frames))
    places = finder.merge_places(results, poses)
    chosen, looks = None, 0
    if places and not finder.zoom():
        chosen = places[0]
    for place in places[:finder.MAX_CLOSER] if finder.zoom() else []:
        looks += 1
        aim = finder.aim(place)
        frame = scene.look(*aim)
        box = finder._close_box(frame, finder.CLOSE_UP, finder.where_in_view(place["yaw"], place["pitch"], *aim))
        checked = finder.look_closer(frame[box].copy(), what)
        if checked.get("yes"):
            chosen = finder.confirmed_place(place, {"frame": frame, "box": box, "head": aim, "checked": checked})
            break
    error = angle_between((chosen["yaw"], chosen["pitch"]), (truth["yaw"], truth["pitch"])) if chosen else None
    return {"present": present, "found": chosen is not None, "error_deg": None if error is None else round(error, 2),
            "pointed": bool(present and chosen and error is not None and error <= POINTED_DEG),
            "places": len(places), "closer_looks": looks, "seconds": round(time.monotonic() - started, 2),
            "truth_deg": [round(math.degrees(truth["yaw"]), 1), round(math.degrees(truth["pitch"]), 1)]}


def summary(rows: list) -> dict:
    pos = [r for r in rows if r["present"]]
    neg = [r for r in rows if not r["present"]]
    k = sum(r["pointed"] for r in pos)
    errors = [r["error_deg"] for r in pos if r["found"] and r["error_deg"] is not None]
    false = sum(r["found"] for r in neg)
    out = {"trials": len(rows), "present": len(pos), "pointed": k,
           "pointed_95": [round(v * 100, 1) for v in wilson(k, len(pos))] if pos else None,
           "found_elsewhere": sum(1 for r in pos if r["found"] and not r["pointed"]),
           "absent": len(neg), "false_finds": false,
           "false_finds_95": [round(v * 100, 1) for v in wilson(false, len(neg))] if neg else None,
           "error_deg_median": percentile(errors, 50), "error_deg_p90": percentile(errors, 90),
           "seconds_median": percentile([r["seconds"] for r in rows], 50)}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--absent", type=float, default=0.2, help="share of trials with the duck out of sight")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--what", default="rubber duck")
    ap.add_argument("--zoom", default="on", choices=["on", "off"])
    ap.add_argument("--duck-scale", type=float, default=1.0, help="the duck's size; 0.35 is about a pair of glasses")
    ap.add_argument("--close-up", type=float, default=None, help="the close-up's share of the frame (finder.CLOSE_UP)")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)
    if vision.eyes() is None:              # before the scene is built: a clear line, not a traceback
        print("Needs NEBIUS_API_KEY (a Nebius Token Factory key): NVIDIA Nemotron 3.5 Super VL reads what Andy sees.",
              file=sys.stderr)
        return 2
    os.environ["ANDY_FINDER_ZOOM"] = args.zoom
    if args.close_up:
        finder.CLOSE_UP = args.close_up
    scene = Scene(args.seed, args.duck_scale)
    rng = random.Random(args.seed + 1000)
    rows = []
    for i in range(args.trials):
        rows.append(trial(scene, rng.random() >= args.absent, args.what))
        r = rows[-1]
        print(f"trial {i + 1}: {'present' if r['present'] else 'absent '} found={r['found']} pointed={r['pointed']} "
              f"error={r['error_deg']} places={r['places']} closer={r['closer_looks']} {r['seconds']} s", flush=True)
    card = {"ran": datetime.now().astimezone().isoformat(timespec="seconds"), "eyes": vision.name(),
            "zoom": args.zoom, "what": args.what, "seed": args.seed, "pointed_deg": POINTED_DEG,
            "duck_scale": args.duck_scale, "close_up": finder.CLOSE_UP,
            "scene": "Pollen's Reachy Mini MuJoCo scene 'minimal' (reachy_mini 1.12.0rc1), MuJoCo 3.3.0",
            "where": os.environ.get("ANDY_SIM_WHERE", "this computer"),
            "summary": summary(rows), "rows": rows}
    try:
        scene.renderer.close()                  # before the interpreter's own teardown, which EGL dislikes
    except Exception:
        pass
    s = card["summary"]
    print(f"Pointed at the duck {s['pointed']} of {s['present']} {s['pointed_95']}; false finds {s['false_finds']} of "
          f"{s['absent']}; pointing error median {s['error_deg_median']} deg")
    text = json.dumps(card, indent=1) + "\n"
    if args.out == "-":
        print("SIM_SCORECARD " + json.dumps(card))
    else:
        small = "" if args.duck_scale == 1.0 else f"-small{args.duck_scale}"
        name = f"sim-finder-{datetime.now():%Y-%m-%d-%H%M}-{args.zoom}{small}.json"
        out = Path(args.out) if args.out else HERE.parent / "evals" / "results" / name
        out.write_text(text)
        print(f"Scorecard: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
