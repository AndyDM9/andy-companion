import io
import json

import pytest

from andy_companion import settings, setup_page, web


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setenv("TAVILY_API_KEY", "k")


def tavily(answers):
    sent = []

    def opener(req, timeout=None):
        body = json.loads(req.data)
        sent.append((req.full_url.rsplit("/", 1)[1], body))
        return io.BytesIO(json.dumps(answers[len(sent) - 1]).encode())
    return opener, sent


def test_the_town_s_events_page_is_found_on_its_own_website_with_map():
    opener, sent = tavily([
        {"results": [{"url": "https://www.tripsite.com/sunny-isles"}, {"url": "https://www.harborbay.example/"}]},
        {"base_url": "https://www.harborbay.example", "results": [
            "https://www.harborbay.example/news/2026/10/road-works", "https://www.harborbay.example/calendar/event/1234-tea-dance",
            "https://www.harborbay.example/calendar", "https://www.harborbay.example/parks/pelican-park", "https://www.harborbay.example/contact"]}])
    found = web.find_events_page("Harbor Bay, Florida", opener)
    assert found == {"site": "https://www.harborbay.example", "page": "https://www.harborbay.example/calendar"}
    assert [s[0] for s in sent] == ["search", "map"]
    assert sent[1][1]["url"] == "https://www.harborbay.example" and "calendar" in sent[1][1]["instructions"]


def test_no_official_site_no_suggestion():
    opener, _ = tavily([{"results": [{"url": "https://www.tripsite.com/x"}]}])
    assert web.find_events_page("Nowhere", opener) is None


def test_setting_the_town_offers_the_page_without_changing_anything():
    setup_page.suggest_events_page("Harbor Bay, Florida",
                                   finder=lambda place: {"site": "https://www.harborbay.example", "page": "https://www.harborbay.example/calendar"})
    s = settings.get()
    assert s["events_suggestion"]["page"] == "https://www.harborbay.example/calendar" and s["events_pages"] == []
    assert setup_page.state()["events_suggestion"]["for"] == "Harbor Bay, Florida"
    setup_page.suggest_events_page("Somewhere", finder=lambda place: (_ for _ in ()).throw(web.WebError("x")))
    assert settings.get()["events_suggestion"] is None


def test_a_site_that_refuses_the_map_is_searched_within_instead():
    opener, sent = tavily([
        {"results": [{"url": "https://www.harborbayfl.gov/"}]},
        {"base_url": "https://www.harborbayfl.gov", "results": []},                       # the site refuses crawlers
        {"results": [{"url": "https://www.harborbayfl.gov/Parks-Recreation/Events"}, {"url": "https://www.harborbayfl.gov/news/2026/10/x"}]}])
    found = web.find_events_page("Harbor Bay, Florida", opener)
    assert found == {"site": "https://www.harborbayfl.gov", "page": "https://www.harborbayfl.gov/Parks-Recreation/Events"}
    assert [s[0] for s in sent] == ["search", "map", "search"] and sent[2][1]["include_domains"] == ["harborbayfl.gov"]
