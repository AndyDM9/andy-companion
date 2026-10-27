"""Run the screen's actual polling code with invented responses and a controlled clock; no network."""
from pathlib import Path
import re
import shutil
import subprocess

import pytest

PAGE = (Path(__file__).resolve().parents[1] / "src/andy_companion/pages/screen.html").read_text()
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(not NODE, reason="node is not installed")


def piece(pattern):
    return re.search(pattern, PAGE, re.S).group(0)


POLLING = "\n".join([
    piece(r"  let ticking = .*?;"),
    piece(r'  let liveNow = .*?;'),
    piece(r'  let lastState = .*?;'),
    piece(r'  const OFFLINE_AFTER_MS = .*?;'),
    piece(r'  async function tick\(\) \{.*?\n  \}'),
    piece(r'  function setOffline\(on\) \{.*?\n  \}'),
    piece(r'  function everySecond\(\) \{.*?\n  \}'),
    piece(r'  async function stateTick\(\) \{.*?\n  \}'),
])
HARNESS = r'''
const assert = require('node:assert/strict');
let now = 0, renders = 0, clockRenders = 0;
const performance = {now: () => now}, token = 'invented-token';
const classes = new Set(), elements = new Map();
const document = {body: {classList: {
  contains: key => classes.has(key),
  toggle: (key, on) => on ? classes.add(key) : classes.delete(key)
}}};
const $ = id => {
  if (!elements.has(id)) elements.set(id, {dataset: {}, textContent: '', offsetWidth: 0,
                                         classList: {remove: () => {}, add: () => {}}});
  return elements.get(id);
};
const text = (element, value) => {element.textContent = value;};
const ui = {lost: 'Not connected', looking: {left: 'Looking left'}};
const showAsk = () => {}, render = () => {renders++;}, renderClock = () => {clockRenders++;};
let hoodLink = '', timerId = 0, fetch;
const timers = new Map(), window = {AbortController};
const setTimeout = (callback, ms) => {const id = ++timerId; timers.set(id, {callback, ms}); return id;};
const clearTimeout = id => timers.delete(id);
const deferred = () => {let resolve, reject; const promise = new Promise((yes, no) => {
  resolve = yes; reject = no;
}); return {promise, resolve, reject};};
const answer = (state = 'ready', label = 'Listening for you') => ({ok: true,
  json: async () => ({state, label, looking: ''})});
const flush = async () => {for (let i = 0; i < 8; i++) await Promise.resolve();};
'''


def run(body):
    code = HARNESS + POLLING + "\n(async () => {\n" + body + "\n})().catch(error => {console.error(error); process.exitCode = 1;});"
    result = subprocess.run([NODE, "-e", code], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_stalled_status_request_does_not_accumulate_and_next_poll_resumes():
    run("""
      let calls = 0; const gate = deferred();
      fetch = () => {calls++; return calls === 1 ? gate.promise : Promise.resolve(answer());};
      const first = stateTick();
      for (let i = 0; i < 30; i++) await stateTick();
      assert.equal(calls, 1);
      gate.resolve(answer()); await first;
      assert.equal(timers.size, 0);
      await stateTick(); assert.equal(calls, 2);
      assert.equal($('state').dataset.state, 'ready');
    """)


@pytest.mark.parametrize("failure", ["throw new Error('invented network failure')",
    "return {ok:false, json:()=>assert.fail('non-OK body read')}",
    "return {ok:true, json:async()=>{throw new Error('invented invalid JSON')}}"])
def test_failed_status_response_releases_poll_guard(failure):
    run("""
      let calls = 0;
      fetch = async () => {calls++; if (calls === 1) {FAILURE;} return answer();};
      await stateTick(); assert.equal(timers.size, 0);
      await stateTick(); assert.equal(calls, 2);
      assert.equal($('state').dataset.state, 'ready');
    """.replace("FAILURE", failure))


@pytest.mark.parametrize("phase", ["headers", "body"])
def test_five_second_timeout_covers_headers_and_body_then_polling_resumes(phase):
    run("""
      let calls = 0, signal; const gate = deferred();
      fetch = async (url, options) => {
        calls++; if (calls > 1) return answer();
        signal = options.signal;
        signal.addEventListener('abort', () => gate.reject(new Error('invented abort')));
        return PHASE === 'headers' ? gate.promise : {ok:true, json:()=>gate.promise};
      };
      const pending = stateTick(); await flush();
      assert.equal(timers.size, 1);
      const timer = [...timers.values()][0]; assert.equal(timer.ms, 5000);
      timer.callback(); await pending;
      assert.equal(signal.aborted, true); assert.equal(timers.size, 0);
      await stateTick(); assert.equal(calls, 2);
      assert.equal($('state').dataset.state, 'ready');
    """.replace("PHASE", repr(phase)))


def test_status_polls_pause_while_offline_and_resume_on_reconnect():
    run("""
      let calls = 0; fetch = async () => {calls++; return answer();};
      setOffline(true);
      for (let i = 0; i < 10; i++) await stateTick();
      assert.equal(calls, 0); assert.equal($('state').dataset.state, 'away');
      assert.equal($('state-label').textContent, 'Not connected');
      setOffline(false); await stateTick();
      assert.equal(calls, 1); assert.equal($('state').dataset.state, 'ready');
    """)


@pytest.mark.parametrize("reconnect", [False, True])
def test_late_json_cannot_overwrite_a_disconnect_or_a_new_connection(reconnect):
    run("""
      const gate = deferred(); let calls = 0;
      fetch = async () => {calls++; return calls === 1 ? {ok:true,json:()=>gate.promise} : answer();};
      const pending = stateTick(); await flush();
      setOffline(true); if (RECONNECT) setOffline(false);
      gate.resolve({state:'speaking',label:'Invented old reply',looking:'left'}); await pending;
      assert.equal($('state').dataset.state, 'away');
      assert.equal($('state-label').textContent, 'Not connected');
      assert.equal($('looking').textContent, '');
      assert.equal(liveNow, ''); assert.equal(lastSpoke, 0);
      setOffline(false); await stateTick();
      assert.equal(calls, 2); assert.equal($('state').dataset.state, 'ready');
      assert.equal($('state-label').textContent, 'Listening for you');
    """.replace("RECONNECT", str(reconnect).lower()))


def test_missing_abort_controller_still_caps_pending_status_requests():
    run("""
      window.AbortController = null;
      const gate = deferred(); let calls = 0;
      fetch = () => {calls++; return gate.promise;};
      const pending = stateTick();
      for (let i = 0; i < 20; i++) await stateTick();
      assert.equal(calls, 1); assert.equal(timers.size, 0);
      gate.resolve(answer()); await pending;
      assert.equal($('state').dataset.state, 'ready');
    """)


def test_stalled_status_does_not_block_main_screen_refresh():
    run("""
      const gate = deferred(); let statusCalls = 0, screenCalls = 0;
      fetch = async url => {
        if (url.startsWith('/api/state?')) {statusCalls++; return gate.promise;}
        screenCalls++; return {ok:true,json:async()=>({})};
      };
      const pending = stateTick(); await tick(); await tick();
      assert.equal(statusCalls, 1); assert.equal(screenCalls, 2); assert.equal(renders, 2);
      gate.resolve(answer()); await pending;
      assert.equal(timers.size, 0);
    """)


def test_main_refresh_deadline_still_marks_offline_and_keeps_clock_running():
    run("""
      let calls = 0; fetch = async () => {calls++; return answer();};
      now = 10001; everySecond();
      assert.equal(clockRenders, 1); assert.equal(classes.has('offline-on'), true);
      assert.equal($('state').dataset.state, 'away');
      await stateTick(); assert.equal(calls, 0);
    """)
