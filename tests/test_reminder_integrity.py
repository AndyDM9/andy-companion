"""Invented reminders only: reject ambiguous times and preserve malformed stores."""
import concurrent.futures
import json
import os
import stat
import threading
from datetime import datetime

import pytest

from andy_companion import board, kept, moments, places, reminders, settings

NOW = datetime(2026, 10, 27, 12, 0)
VALID = {'id': 'invented', 'text': 'Water the invented plant', 'due': NOW.timestamp(), 'repeat': None}


@pytest.fixture
def store(tmp_path, monkeypatch):
    path = tmp_path / 'reminders.json'
    monkeypatch.setattr(reminders, 'STORE', path)
    return path


@pytest.mark.parametrize('kwargs', [
    {'minutes': 1, 'at': '08:00'}, {'minutes': True}, {'minutes': False},
    {'minutes': float('nan')}, {'minutes': float('inf')}, {'minutes': float('-inf')},
    {'minutes': {}}, {'minutes': 'invented-private-input'}, {'minutes': 10**1000},
    {'at': '08:0'}, {'at': True}, {'at': '08:00:00'}, {'at': '24:00'},
])
def test_invalid_or_ambiguous_time_never_writes_a_reminder(store, kwargs):
    with pytest.raises(ValueError) as error:
        reminders.add('Water the invented plant', now=NOW, **kwargs)
    assert not store.exists()
    assert 'invented-private-input' not in str(error.value)


def test_conflicting_daily_time_is_rejected_instead_of_becoming_one_minute_from_now(store):
    with pytest.raises(ValueError, match='one reminder time'):
        reminders.add('Water the invented plant', minutes=1, at='08:00', repeat='daily', now=NOW)
    assert not store.exists()
    item = reminders.add('Water the invented plant', at='08:00', repeat='daily', now=NOW)
    assert datetime.fromtimestamp(item['due']) == datetime(2026, 10, 28, 8, 0)


@pytest.mark.parametrize('items', [
    [None], [dict(VALID, due='not-a-time')], [dict(VALID, due=1e300)],
    [dict(VALID, due=float('nan'))], [dict(VALID, due=float('inf'))], [dict(VALID, due=True)],
    [dict(VALID, created='not-a-time')], [dict(VALID, repeat='weekly')],
    [dict(VALID, id='')], [dict(VALID, text='')], [dict(VALID, text={})],
    [dict(VALID, text='x' * 201)], [VALID, dict(VALID)], [{'text': 'Invented text'}],
    [VALID, None], {'reminders': [VALID]},
])
def test_malformed_rows_are_preserved_without_breaking_reads(store, items, caplog):
    payload = json.dumps(items).encode()
    store.write_bytes(payload)
    os.chmod(store, 0o600)
    assert reminders.pending() == []
    copies = reminders.recovery_files()
    assert len(copies) == 1 and not store.exists()
    copy = store.parent / copies[0]['id']
    assert copy.read_bytes() == payload and stat.S_IMODE(copy.stat().st_mode) == 0o600
    assert 'Water the invented plant' not in caplog.text and 'Invented text' not in caplog.text
    assert reminders.pending() == []  # a second reader does not re-quarantine it


def test_legacy_one_off_without_optional_metadata_keeps_its_existing_format(store):
    item = {k: v for k, v in VALID.items() if k != 'repeat'}
    store.write_text(json.dumps([item]))
    assert reminders.pending() == [item] and reminders.recovery_files() == []


def test_a_generated_identifier_collision_does_not_create_an_invalid_store(store, monkeypatch):
    reminders._save([VALID])
    candidates = iter(['invented', 'fresh1'])
    monkeypatch.setattr(reminders.secrets, 'token_hex', lambda n: next(candidates))
    item = reminders.add('Another invented task', minutes=5, now=NOW)
    assert item['id'] == 'fresh1'
    assert len(reminders.pending()) == 2 and not reminders.recovery_files()


def test_identifier_retry_is_bounded_and_cannot_overwrite_existing_data(store, monkeypatch):
    reminders._save([VALID])
    original = store.read_bytes()
    monkeypatch.setattr(reminders.secrets, 'token_hex', lambda n: 'invented')
    with pytest.raises(ValueError, match='No new reminder'):
        reminders.add('Another invented task', minutes=5, now=NOW)
    assert store.read_bytes() == original


def test_same_second_recovery_never_overwrites_an_earlier_copy(store, monkeypatch):
    monkeypatch.setattr(reminders.time, 'time', lambda: 123)
    for payload in [b'first invented damaged file', b'second invented damaged file']:
        store.write_bytes(payload)
        assert reminders.pending() == []
    assert {p.read_bytes() for p in store.parent.glob('reminders.unreadable-*.json')} == {
        b'first invented damaged file', b'second invented damaged file'}


def test_failure_to_preserve_the_original_prevents_a_new_write(store, monkeypatch):
    payload = b'invented damaged file'
    store.write_bytes(payload)
    replace = reminders.os.replace

    def fail_source(src, dst):
        if src == store:
            raise OSError('invented-private-error')
        return replace(src, dst)

    monkeypatch.setattr(reminders.os, 'replace', fail_source)
    with pytest.raises(ValueError, match='No reminder changes') as error:
        reminders.add('Water the invented plant', minutes=5, now=NOW)
    assert 'invented-private-error' not in str(error.value)
    assert store.read_bytes() == payload and reminders.recovery_files() == []


@pytest.mark.parametrize('failure', ['replace', 'nonfinite'])
def test_failed_atomic_save_leaves_no_temporary_copy(store, monkeypatch, failure):
    reminders._save([VALID])
    original = store.read_bytes()
    if failure == 'replace':
        def fail(*args):
            raise OSError('invented error')
        monkeypatch.setattr(reminders.os, 'replace', fail)
        error = OSError
        data = [dict(VALID, text='A changed invented task')]
    else:
        error = ValueError
        data = [dict(VALID, due=float('nan'))]
    with pytest.raises(error):
        reminders._save(data)
    assert store.read_bytes() == original and list(store.parent.glob('*.tmp')) == []


def test_reads_wait_for_a_cooperating_writer(store):
    store.write_text('[]')
    started = threading.Event()

    def read():
        started.set()
        return reminders.pending()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        with reminders._locked():
            future = pool.submit(read)
            assert started.wait(1)
            with pytest.raises(concurrent.futures.TimeoutError):
                future.result(timeout=0.05)
        assert future.result(timeout=2) == []


def test_recovery_is_visible_deletable_and_included_in_delete_everything(store, tmp_path, monkeypatch):
    monkeypatch.setattr(board, '_transient', lambda *args, **kwargs: kwargs.get('default'))
    for name in ('SCREEN', 'SHARED', 'INBOX', 'TOKENS'):
        monkeypatch.setattr(board, name, tmp_path / f'{name.lower()}.json')
    monkeypatch.setattr(board, 'PHOTOS', tmp_path / 'photos')
    monkeypatch.setattr(settings, 'FILE', tmp_path / 'settings.json')
    monkeypatch.setattr(moments, 'FILE', tmp_path / 'moments.json')
    monkeypatch.setattr(places, 'FILE', tmp_path / 'places.json')
    monkeypatch.setattr(kept, 'MEMORY_FILE', tmp_path / 'memory.json')
    store.write_text('[null]')
    summary = kept.summary()
    assert summary['reminder'] == [] and len(summary['recovery']) == 1
    recovery = summary['recovery'][0]
    assert '[null]' not in json.dumps(recovery)
    outside = tmp_path / 'outside.json'
    outside.write_text('invented unrelated file')
    assert not kept.delete('recovery', '../outside.json') and outside.exists()
    assert kept.delete('recovery', recovery['id']) and not kept.summary()['recovery']
    store.write_text('[null]')
    counts = kept.delete_everything()
    assert counts['recovery'] == 1 and not reminders.recovery_files()
    assert kept.words_for({'recovery': 1}) == ['a saved reminder copy needing review']
    assert outside.exists()
