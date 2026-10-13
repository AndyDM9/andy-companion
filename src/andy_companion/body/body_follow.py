"""Turn Andy's body to face the person they are tracking, not only their head.

Pollen's face tracking steers the head only; the base joins only past 65° (a hard limit in
their kinematics), and their maintainers keep head and body detached by design
(reachy_mini_conversation_app PR #157). This adds the pattern community apps use
(reachy_personaplex, reachy_mini_homebody, reachy_mini_megan), inside the one control loop:

- a "facing" angle for the body that, while tracking, eases toward SHARE of where the head
  looks (the head keeps the rest), re-aiming only when that moves by more than HYSTERESIS
  (an effective dead zone of HYSTERESIS / SHARE, ~13°), at most RATE per second, within CLAMP;
- moves (emotions, dances) play relative to that angle and freeze it while they run, so an
  emotion never swings Andy away from the person;
- with tracking off, the body glides back to centre at the same rate.

Pollen's own 65° head-to-body limit and automatic body yaw stay on underneath.
"""

from __future__ import annotations

import os
import math
from typing import Callable, Optional
from dataclasses import dataclass

import numpy as np

ENABLED = os.environ.get("ANDY_BODY_FOLLOW", "on").lower() != "off"


def head_yaw(pose: np.ndarray) -> float:
    """World yaw of a 4x4 head pose built from extrinsic xyz Euler angles (Pollen's convention)."""
    return math.atan2(float(pose[1, 0]), float(pose[0, 0]))


@dataclass
class BodyFollow:
    share: float = 0.6
    hysteresis: float = math.radians(8)
    rate: float = math.radians(30)        # per second
    clamp: float = math.radians(120)
    read_every: float = 0.1               # seconds between head-pose reads
    offset: float = 0.0                   # the body's facing angle now
    target: float = 0.0
    _last_t: Optional[float] = None
    _last_read: float = -1e9
    _last_yaw: Optional[float] = None

    def read_head_yaw(self, now: float, read_pose: Callable[[], np.ndarray]) -> Optional[float]:
        """The head's world yaw, read from the robot at most every read_every seconds."""
        if now - self._last_read >= self.read_every:
            self._last_read = now
            try:
                self._last_yaw = head_yaw(read_pose())
            except Exception:
                self._last_yaw = None
        return self._last_yaw

    def step(self, now: float, head_world_yaw: Optional[float], pose_body_yaw: float,
             tracking: bool, move_owns_body: bool) -> float:
        """The body yaw to command this tick."""
        dt = 0.0 if self._last_t is None else min(max(now - self._last_t, 0.0), 0.1)
        self._last_t = now
        if not move_owns_body:
            if tracking and head_world_yaw is not None:
                desired = max(-self.clamp, min(self.clamp, self.share * head_world_yaw))
                if abs(desired - self.target) > self.hysteresis:
                    self.target = desired
            elif not tracking:
                self.target = 0.0
            step = self.rate * dt
            self.offset += max(-step, min(step, self.target - self.offset))
        return self.offset + pose_body_yaw
