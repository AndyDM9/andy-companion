"""Andy's voice is still playing after the server finishes the reply (2026-10-07)."""

from andy_companion.body import speaking


def test_pushed_audio_keeps_him_speaking_for_its_length():
    speaking.cleared()
    speaking.pushed(24000 * 3, 24000, now=100.0)          # three seconds of voice pushed at once
    assert speaking.speaking(now=102.9) and not speaking.speaking(now=103.5)
    speaking.pushed(12000, 24000, now=101.0)              # more arrives while playing: queued behind
    assert speaking.speaking(now=103.6)


def test_a_barge_in_ends_it():
    speaking.pushed(24000 * 10, 24000, now=200.0)
    speaking.cleared()
    assert not speaking.speaking(now=200.5)
