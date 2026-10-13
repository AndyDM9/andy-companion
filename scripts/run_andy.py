"""Start Pollen's conversation app with Andy's own additions attached: the body behaviours
(looking at the person, body follow, seek, calm idle moments), the reminder and morning-plan speaker,
exact spoken controls, the person's pace and volume, and the privacy floor (no conversation text in any log; Andy's own memory store)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from andy_companion import privacy, settings, speaker, voice_controls, volume  # noqa: E402
from andy_companion.body import attach as body  # noqa: E402

privacy.install()
body.install()
speaker.attach()
settings.install()
voice_controls.install()
volume.apply_saved()

from reachy_mini_conversation_app.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
