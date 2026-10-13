from datetime import datetime

from andy_companion import clock


def test_says_the_day_date_and_time_in_words():
    now = datetime(2026, 10, 13, 12, 50)
    told = clock.today(now)
    assert told["weekday"] == "Tuesday"
    assert told["date"] == "13 October 2026"
    assert told["time"] == "12:50"
    assert told["part_of_day"] == "afternoon"
    assert "Tuesday 13 October 2026" in told["say"]


def test_part_of_day_boundaries():
    assert clock.part_of_day(datetime(2026, 1, 1, 5, 0)) == "morning"
    assert clock.part_of_day(datetime(2026, 1, 1, 11, 59)) == "morning"
    assert clock.part_of_day(datetime(2026, 1, 1, 12, 0)) == "afternoon"
    assert clock.part_of_day(datetime(2026, 1, 1, 17, 0)) == "evening"
    assert clock.part_of_day(datetime(2026, 1, 1, 22, 0)) == "night"
    assert clock.part_of_day(datetime(2026, 1, 1, 3, 0)) == "night"
