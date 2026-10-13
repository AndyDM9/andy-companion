"""Start Pollen's conversation app with Andy's own additions attached (see andy_companion.app_mode):
the body behaviours, the reminder and morning-plan speaker, exact spoken controls, the urgent-words
net, captions, the person's pace and volume, and the privacy floor."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from andy_companion import app_mode  # noqa: E402

app_mode.install()

from reachy_mini_conversation_app.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
