"""Invented credential labels never reach a memory write or a spoken proposal."""
import json

import pytest

from andy_companion import consent


@pytest.mark.parametrize('payload', [
    'My password is demo-only-not-a-real-password.',
    'Contraseña: ejemplo-inventado.',
    'Bank PIN 0000',
    'Mi PIN es 0000',
    'Credit card number: 0000 0000 0000 0000',
    'Número de tarjeta = 0000 0000 0000 0000',
    'CVV: 000',
    'API key is invented-test-value',
    'access token = invented-test-value',
])
@pytest.mark.parametrize('name,field', [
    ('remember', 'fact'), ('remember_fact', 'fact'),
    ('remember_moment', 'what'), ('remember_place', 'said_where'),
])
def test_labelled_credentials_are_refused_even_after_an_explicit_request(payload, name, field):
    gate = consent.Confirmation()
    gate.hear('Please remember this test detail.')
    result = gate.authorize(name, {field: payload})
    assert result['saved'] is False and result['reason'] == 'credential_value'
    assert not result.get('confirmation_needed') and gate.pending is None
    assert payload not in json.dumps(result)


@pytest.mark.parametrize('fact', [
    'Reset my password on Friday.', 'I forgot my password.',
    'My bank card is in the drawer.', 'The PIN reminder letter is on the desk.',
    'My cousin visits on Friday.', 'La tarjeta está en el cajón.',
])
def test_ordinary_account_talk_and_facts_keep_the_existing_consent_path(fact):
    gate = consent.Confirmation()
    gate.hear('Please remember this test detail.')
    assert gate.authorize('remember_fact', {'fact': fact}) is None


def test_rejected_secret_clears_an_earlier_proposal_and_cannot_be_confirmed():
    gate = consent.Confirmation()
    gate.hear('I enjoy gardening.')
    proposal = gate.authorize('remember_fact', {'fact': 'Enjoys gardening.'})
    gate.said(proposal['say'])
    gate.hear('Yes please')
    assert gate.authorize('remember_fact', {'fact': 'Password: invented-only'})['saved'] is False
    assert gate.pending is None and not gate.confirmed
    assert gate.authorize('remember_fact', {'fact': 'Enjoys gardening.'})['saved'] is False
