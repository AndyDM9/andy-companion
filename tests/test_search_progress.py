"""Synthetic progress across the memory-only screen boundary; no camera or robot connection."""
import pytest

from andy_companion import board, transient


def test_progress_has_no_target_text_or_private_id_on_the_screen(tmp_path, monkeypatch):
    monkeypatch.setattr(board, 'SCREEN', tmp_path / 'screen.json')
    key = board.start_search()
    board.search_step(key, 'reading', 3)
    card = board.showing()
    assert card['kind'] == 'search' and card['stage'] == 'reading' and card['captured'] == 3
    assert 'search_id' not in card and card['title'] == '' and card['items'] == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('replace', ['card', 'clear', 'private', 'new-search'])
def test_late_progress_and_cleanup_cannot_replace_newer_content(replace):
    key = board.start_search()
    if replace == 'card':
        board.show('seen', 'Your glasses', [])
    elif replace == 'clear':
        board.clear_screen()
    elif replace == 'private':
        board.transient_action('clear-private')
    else:
        board.start_search()
    expected = board.showing()
    board.search_step(key, 'closer', 4)
    board.end_search(key)
    assert board.showing() == expected


@pytest.mark.parametrize('stage,count', [('guessing', 2), ('reading', -1), ('reading', 5), ('reading', True), ('reading', '4')])
def test_bad_progress_is_rejected(stage, count):
    key = board.start_search()
    with pytest.raises(ValueError, match='Bad search progress'):
        board.search_step(key, stage, count)


def test_stalled_progress_expires_and_cannot_be_revived(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(board.time, 'time', lambda: now[0])
    key = board.start_search()
    now[0] += board.SEARCH_FOR_S + 1
    board.search_step(key, 'reading', 4)
    assert board.showing() is None
    board.search_step(key, 'closer', 4)
    assert board.showing() is None


def test_each_real_step_renews_the_short_expiry(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(board.time, 'time', lambda: now[0])
    key = board.start_search()
    now[0] += 20
    board.search_step(key, 'scanning', 1)
    assert board.showing(now=1050)['captured'] == 1
    assert board.showing(now=1066) is None


def test_unavailable_screen_never_prevents_the_finder(monkeypatch):
    def unavailable(*args):
        raise transient.Unavailable()
    monkeypatch.setattr(transient, 'call', unavailable)
    key = board.start_search()
    assert key is None
    board.search_step(key, 'reading', 4)
    board.end_search(key)


def test_progress_crosses_the_actual_loopback_boundary(tmp_path, monkeypatch):
    from andy_companion import screen_server

    monkeypatch.setattr(board, 'TOKENS', tmp_path / 'tokens.json')
    httpd = screen_server.serve('127.0.0.1', 0)
    monkeypatch.setenv('ANDY_SCREEN_PORT', str(httpd.server_address[1]))
    monkeypatch.setattr(transient, 'owner', False)
    try:
        key = board.start_search()
        assert isinstance(key, str)
        board.search_step(key, 'closer', 4)
        assert board.showing()['stage'] == 'closer'
        assert 'search_id' not in board.showing()
        board.end_search(key)
        assert board.showing() is None
    finally:
        httpd.shutdown()
