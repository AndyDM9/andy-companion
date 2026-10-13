"""Andy Companion as a Reachy Mini app: Pollen's conversation app with all of Andy attached.

Andy's voice server must be reachable (ANDY_VOICE_URL, default ws://127.0.0.1:8765/v1/realtime).
In the dashboard there is no supervisor, so sleep and quiet stop the app; start it again from
the dashboard. Reminders still need the app running to be said.
"""

import threading

from reachy_mini import ReachyMini
from reachy_mini_conversation_app.main import ReachyMiniConversationApp

from andy_companion import app_mode


class AndyCompanionApp(ReachyMiniConversationApp):
    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event) -> None:
        app_mode.install(screen=True)
        super().run(reachy_mini, stop_event)


if __name__ == "__main__":
    app = AndyCompanionApp()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()
