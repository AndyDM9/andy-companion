"""Start Pollen's conversation app with Andy's own additions attached: the body behaviours
(looking at the person, body follow, seek, calm idle moments) and the reminder speaker."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from andy_companion import speaker  # noqa: E402
from andy_companion.body import attach as body  # noqa: E402

body.install()
speaker.attach()

from reachy_mini_conversation_app.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
