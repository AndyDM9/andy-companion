import asyncio

from andy_companion import turns
from andy_companion.body import thinking

TICK = 0.01   # Pollen's control loop runs at about 100 Hz


def run(thinker, start, seconds, active, base=(-0.17, 0.17)):
    out, now = [], start
    while now < start + seconds - 1e-9:
        out.append(thinker.step(now, base, active))
        now += TICK
    return out, now


def test_not_thinking_leaves_the_antennas_alone():
    out, _ = run(thinking.Thinking(), 0.0, 2.0, False)
    assert set(out) == {(-0.17, 0.17)}


def test_thinking_leans_both_antennas_together_and_smoothly():
    t = thinking.Thinking()
    out, now = run(t, 0.0, 3.0, True)
    out2, _ = run(t, now, 1.0, False)
    poses = out + out2
    steps = [max(abs(a[0] - b[0]), abs(a[1] - b[1])) for a, b in zip(poses, poses[1:])]
    assert max(steps) / TICK < 1.0                       # rad/s: well under the antennas' 2 rad/s
    assert max(abs(p[0] + 0.17) for p in out) > 0.2      # a lean anyone can see
    assert all(abs((p[0] + 0.17) - (p[1] - 0.17)) < 1e-9 for p in poses)   # together, not mirrored
    assert out2[-1] == (-0.17, 0.17)                     # fully back once Andy speaks


def test_andy_is_thinking_from_understood_words_to_the_first_sound():
    ticks = [100.0]
    clock = turns.TurnClock(clock=lambda: ticks[0])
    assert not clock.thinking()
    clock.mark("user_speech_stopped")
    assert not clock.thinking()                          # still hearing
    clock.mark("user_transcription_completed")
    assert clock.thinking()
    ticks[0] = 100.8
    clock.mark("assistant_audio_delta")
    assert not clock.thinking()


def test_a_long_silence_is_not_thinking_forever():
    ticks = [100.0]
    clock = turns.TurnClock(clock=lambda: ticks[0])
    clock.mark("user_transcription_completed")
    ticks[0] = 125.0
    assert not clock.thinking()


def test_a_running_tool_is_thinking_even_after_andy_spoke():
    class Handler:
        def _mark_activity(self, reason):
            pass

    seen = []
    clock = turns.TurnClock()

    class Routine:
        tool_name = "describe_view"

        async def __call__(self, manager):
            seen.append(clock.thinking())
            return {}

    turns.install(Handler, Routine, clock)
    clock.mark("user_transcription_completed")
    clock.mark("assistant_audio_delta")                 # "Let me look."
    asyncio.run(Routine()(None))
    assert seen == [True] and clock.running == 0 and not clock.thinking()
