"""Invented completion envelopes; rejected provider data never becomes an answer."""
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from andy_companion import deeper, letters, scamcheck, vision
from andy_companion.model_reply import ModelReplyError, final_object, final_text

MARKER = 'invented-private-provider-draft'


def completion(content='An invented final answer.', **choice):
    return {'choices': [{'finish_reason': 'stop', 'message': {'content': content}, **choice}]}


@pytest.mark.parametrize('payload', [
    None, [], {}, {'choices': None}, {'choices': {}}, {'choices': []}, {'choices': [None]},
    {'choices': [{'message': None}]}, {'choices': [{'message': {}}]},
    completion(None), completion(12), completion(False), completion([]), completion({'draft': MARKER}),
    completion(''), completion(' \n\t'), completion(MARKER, finish_reason='length'),
    completion(MARKER, finish_reason='content_filter'), completion(MARKER, finish_reason=None),
    completion(MARKER, finish_reason='tool_calls'),
    completion(message={'content': MARKER, 'refusal': 'An invented refusal'}),
    completion(message={'content': MARKER, 'tool_calls': [{'id': 'invented'}]}),
    completion(message={'content': MARKER, 'function_call': {'name': 'invented'}}),
    completion('<think>'+MARKER), completion('<THINK>'+MARKER), completion('<think'),
    completion('<think>'+MARKER+'</think>'), completion(MARKER+'</think'),
    completion('<think>draft</think>Final text<think>unfinished'),
])
def test_invalid_or_incomplete_replies_cannot_be_final_text(payload, caplog):
    with pytest.raises(ModelReplyError) as error:
        final_text(payload)
    assert MARKER not in str(error.value) and MARKER not in caplog.text


@pytest.mark.parametrize('content', [
    'An invented final answer.',
    '<think>'+MARKER+'</think>An invented final answer.',
    MARKER+'</think>An invented final answer.',
    '<THINK>'+MARKER+'</THINK>\n An invented final answer. ',
])
def test_complete_final_suffix_is_used_without_the_reasoning(content):
    assert final_text(completion(content)) == 'An invented final answer.'


def test_separate_reasoning_fields_are_not_returned():
    data = completion(message={'content': 'An invented final answer.', 'reasoning_content': MARKER, 'reasoning': MARKER})
    assert final_text(data) == 'An invented final answer.'


def test_legacy_compatible_envelopes_without_finish_reason_remain_accepted():
    assert final_text({'choices': [{'message': {'content': 'An invented final answer.'}}]}) == 'An invented final answer.'


def test_structured_content_keeps_literal_tag_strings_for_its_own_json_validator():
    text = json.dumps({'about': 'A literal </think> tag', 'note': '<think> is printed on the page'})
    assert json.loads(final_text(completion(text), structured=True))['about'] == 'A literal </think> tag'


@pytest.mark.parametrize('value', [
    [], None, {}, {'sign': 'none'}, {'sign': False, 'evidence': '', 'source': ''},
    {'sign': 'unknown-enum', 'evidence': '', 'source': ''},
    {'sign': 'none', 'evidence': {}, 'source': ''},
    {'sign': 'none', 'evidence': '', 'source': '', 'extra': MARKER},
])
def test_wrong_sign_fields_cannot_become_a_no_sign_verdict(monkeypatch, value):
    monkeypatch.setenv('NEBIUS_API_KEY', 'invented-not-used')
    def opener(*args, **kwargs):
        return io.BytesIO(json.dumps(completion(json.dumps(value))).encode())
    with pytest.raises(scamcheck.ScamCheckError):
        scamcheck.verdict('An invented ordinary message', opener=opener)


@pytest.mark.parametrize('value', [{}, [], {'matches': None}, {'matches': [True]}, {'matches': ['1']},
                                   {'matches': [1.5]}, {'matches': [], 'extra': MARKER}])
def test_wrong_warning_match_fields_are_not_silently_treated_as_no_matches(monkeypatch, value):
    monkeypatch.setenv('NEBIUS_API_KEY', 'invented-not-used')
    def opener(*args, **kwargs):
        return io.BytesIO(json.dumps(completion(json.dumps(value))).encode())
    with pytest.raises(scamcheck.ScamCheckError):
        scamcheck._ask('Invented instruction', 'Invented message', scamcheck.MATCH_SCHEMA, opener, 'invented')


@pytest.mark.parametrize('value', [{}, [], {'kind': 'notice'},
                                   {'kind': 'notice', **{k: '' for k in letters.FIELDS}, 'suspicious': 'false'},
                                   {'kind': 'unknown-enum', **{k: '' for k in letters.FIELDS}, 'suspicious': False}])
def test_wrong_letter_fields_cannot_become_a_completed_card(monkeypatch, value):
    monkeypatch.setenv('NEBIUS_API_KEY', 'invented-not-used')
    def opener(*args, **kwargs):
        return io.BytesIO(json.dumps(completion(json.dumps(value))).encode())
    with pytest.raises(letters.LetterError):
        letters.summarise('An invented notice', opener=opener)


def test_typed_objects_preserve_valid_false_empty_arrays_and_literal_tag_values():
    value = {'label': 'A literal </think> tag', 'flag': False, 'matches': []}
    assert final_object(completion(json.dumps(value)), strings=('label',), booleans=('flag',),
                        integer_arrays=('matches',)) == value


@pytest.mark.parametrize('client', ['deeper', 'vision', 'letters', 'scamcheck'])
@pytest.mark.parametrize('content,reason', [(None, 'stop'), ({'draft': MARKER}, 'stop'),
                                          ('An unfinished answer', 'length'), ('', 'stop')])
def test_actual_clients_turn_bad_provider_envelopes_into_errors(monkeypatch, client, content, reason):
    monkeypatch.setenv('NEBIUS_API_KEY', 'invented-not-used')

    def opener(*args, **kwargs):
        return io.BytesIO(json.dumps(completion(content, finish_reason=reason)).encode())

    endpoint = {'name': 'local', 'url': 'http://127.0.0.1:1', 'token': '', 'model': 'invented', 'extra': {}}
    call, error = {
        'deeper': (lambda: deeper.think('An invented choice', opener=opener), deeper.DeeperError),
        'vision': (lambda: vision._ask(endpoint, [], 20, 0, None, opener), ModelReplyError),
        'letters': (lambda: letters.summarise('An invented meeting notice', opener=opener), letters.LetterError),
        'scamcheck': (lambda: scamcheck.verdict('An invented message', opener=opener), scamcheck.ScamCheckError),
    }[client]
    with pytest.raises(error) as problem:
        call()
    assert MARKER not in str(problem.value)


@pytest.mark.parametrize('client', ['letters', 'scamcheck'])
@pytest.mark.parametrize('reason', ['length', 'content_filter'])
def test_even_parseable_json_cannot_override_an_incomplete_or_filtered_result(monkeypatch, client, reason):
    monkeypatch.setenv('NEBIUS_API_KEY', 'invented-not-used')

    def opener(*args, **kwargs):
        return io.BytesIO(json.dumps(completion('{}', finish_reason=reason)).encode())

    if client == 'letters':
        with pytest.raises(letters.LetterError):
            letters.summarise('An invented meeting notice', opener=opener)
    else:
        with pytest.raises(scamcheck.ScamCheckError):
            scamcheck.verdict('An invented message', opener=opener)


def test_malformed_primary_reply_does_not_trigger_a_different_model(monkeypatch):
    endpoint = {'name': 'token-factory', 'url': 'https://model.example/v1', 'token': '', 'model': 'invented', 'extra': {}}
    monkeypatch.setattr(vision, 'fallback', lambda primary: {'name': 'local'})
    calls = []

    def opener(request, **kwargs):
        calls.append(request.full_url)
        return io.BytesIO(json.dumps(completion(None)).encode())

    before = vision.used()
    with pytest.raises(ModelReplyError):
        vision.answer(endpoint, [], 20, 0, opener=opener)
    assert calls == [endpoint['url']] and vision.used() == before


@pytest.mark.parametrize('job', ['scam', 'sim'])
def test_cloud_job_copy_manifests_include_the_new_shared_dependency(tmp_path, job):
    root = Path(__file__).resolve().parents[1]
    text = (root/'cloud'/f'{job}-job.sh').read_text()
    if job == 'scam':
        names = set(re.findall(r'\$ROOT/src/andy_companion/(\w+)\.py', text))
        imported = 'scamcheck'
    else:
        names = set(re.search(r'for f in ([\w ]+); do cp', text).group(1).split())
        imported = 'vision'
    assert 'model_reply' in names
    package = tmp_path/'src'/'andy_companion'
    package.mkdir(parents=True)
    for name in names:
        shutil.copyfile(root/'src'/'andy_companion'/f'{name}.py', package/f'{name}.py')
    source = 'import sys; sys.path.insert(0, sys.argv[1]); __import__("andy_companion."+sys.argv[2])'
    subprocess.run([sys.executable, '-I', '-c', source, str(package.parent), imported],
                   check=True, capture_output=True, timeout=10)
