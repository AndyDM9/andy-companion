'use strict';
const $ = id => document.getElementById(id);
let selected, session, busy = false, available = false;
const messages = {
  busy: 'Andy is handling other examples. Please try again shortly.',
  public_allowance_reached: 'The public inference allowance has been used. Please use Testing instructions for free robot access.',
  not_configured: 'Live inference is not configured here. You can still explore the sample screens.',
  session_expired: 'This example expired. Start it again.',
  step_already_handled: 'This choice has already been handled. Start a new example to try the other choice.',
  model_unavailable: 'The model could not answer right now. Please try the example again.',
  model_action_rejected: 'The model requested an action outside this example. Nothing was sent to a real family or robot.'
};
function controls() {
  $('run').disabled = busy || !available || !selected;
  $('yes').disabled = $('no').disabled = busy;
  for (const b of $('challenges').querySelectorAll('button')) b.disabled = busy;
}
function select(item) {
  selected = item; session = null;
  $('sample').textContent = item.sample;
  $('prompt').textContent = 'The invented request: “' + item.prompt + '”';
  $('answer').textContent = $('source').textContent = $('trace').textContent = '';
  $('decision').hidden = true;
  $('family').textContent = 'Sample family page: nothing shared.';
  $('status').textContent = available ? 'Ready. Choose Try this example.' : messages.not_configured;
  for (const b of $('challenges').querySelectorAll('button')) b.setAttribute('aria-pressed', String(b.dataset.id === item.id));
  controls();
}
async function run(choice) {
  if (busy || !selected) return;
  if (!choice) session = null;
  busy = true; controls(); $('decision').hidden = true;
  $('status').textContent = 'Waiting for Nemotron…';
  if (!choice) {
    $('answer').textContent = $('source').textContent = $('trace').textContent = '';
    $('family').textContent = 'Sample family page: nothing shared.';
  }
  try {
    const body = {challenge: selected.id};
    if (choice) { body.session = session; body.choice = choice; }
    const response = await fetch('/api/run', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) throw new Error(messages[data.error] || 'This example could not finish. Start it again.');
    session = data.session;
    $('answer').textContent = data.reply;
    $('source').textContent = 'Reply from ' + data.reply_source + ' · ' + data.seconds + ' s for this web step.';
    $('trace').textContent = data.tools.length ? 'Tool: ' + data.tools.map(t => t.name + ' (simulated effect)').join(', ') : 'No tool action in this step.';
    $('family').textContent = data.sample_family_shared ? 'Sample family page: “I enjoyed the garden today.”' : 'Sample family page: nothing shared.';
    $('decision').hidden = !data.awaiting_choice;
    $('status').textContent = data.awaiting_choice ? 'Nothing shared. Read the exact note, then choose.' : 'Example complete. No additional work is scheduled.';
  } catch (error) {
    $('status').textContent = error.message || 'The connection failed. Please start again.';
  } finally { busy = false; controls(); }
}
$('run').addEventListener('click', () => run());
$('yes').addEventListener('click', () => run('yes'));
$('no').addEventListener('click', () => run('no'));
fetch('/api/status').then(r => r.json()).then(data => {
  available = data.enabled;
  for (const item of data.challenges) {
    const b = document.createElement('button'); b.textContent = item.title; b.dataset.id = item.id;
    b.addEventListener('click', () => select(item)); $('challenges').append(b);
  }
  select(data.challenges[0]);
}).catch(() => { $('status').textContent = 'The examples could not load. Please refresh.'; });
