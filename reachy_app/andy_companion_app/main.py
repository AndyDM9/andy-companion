"""Andy Companion as a Reachy Mini app: Pollen's conversation app with all of Andy attached.

Andy's voice server must be reachable (ANDY_VOICE_URL, default ws://127.0.0.1:8765/v1/realtime).
Keys (Tavily, Token Factory, the eyes' and second look's endpoints) come from the private env file,
~/.config/companion-hackathon/.env or ANDY_ENV_FILE, read by app_mode.install; nothing already set is
replaced. In the dashboard there is no supervisor, so sleep and quiet stop the app, and the watchdog
only logs when it would restart it; start it again from the dashboard. Reminders still need the app
running to be said.

The class inherits ReachyMiniApp directly, as Pollen's app checker (`reachy-mini-app-assistant
check`) requires, and runs Pollen's conversation app the way its own ReachyMiniConversationApp does
(reachy_mini_conversation_app 1.0.1, main.py), with Andy installed first.
"""

import asyncio
import threading

from reachy_mini import ReachyMini, ReachyMiniApp

from andy_companion import app_mode


class AndyCompanionApp(ReachyMiniApp):
    # Pollen's settings page, on this computer only: on 0.0.0.0 (Pollen's own default) anyone on the home
    # network could read the conversation as text and make Andy say anything (review, 2026-10-13).
    custom_app_url = "http://127.0.0.1:7860/"
    dont_start_webserver = False

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event) -> None:
        app_mode.install(screen=True)
        # Pollen constructs its global Config on import. Andy must configure its external profile first.
        from reachy_mini_conversation_app.main import parse_args, run as run_conversation

        asyncio.set_event_loop(asyncio.new_event_loop())
        args, _ = parse_args()
        run_conversation(args, robot=reachy_mini, app_stop_event=stop_event, settings_app=self.settings_app,
                         instance_path=self._get_instance_path().parent)


if __name__ == "__main__":
    app = AndyCompanionApp()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()
