"""Fixed teaching recovery gate. No model, production credentials or external network."""
import json
import urllib.request
import urllib.error
from urllib.parse import urlparse


def http(base, path, payload=None, timeout=2):
    parsed = urlparse(base)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or path not in ('/notify', '/receipt', '/health'):
        raise ValueError('Only fixed paths on the loopback receiver are allowed')
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(base + path, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            return {'http_status': response.status, 'body': json.loads(raw) if raw else None}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return {'http_status': exc.code, 'body': json.loads(raw) if raw else None}


def recover(base, payload, policy, state, audit, proposed='retry'):
    """Policy/state are supplied by the operator, never by the model proposal.

    A failed/absent query is not authoritative negative evidence. A successful
    query must say the previous attempt is closed before a retry is considered.
    This runner is single-process and sequential; it is not a distributed lock.
    """
    def finish(action, reason):
        result = {'action': action, 'reason': reason, 'proposal': proposed}
        audit.append(result)
        return result
    if policy.get('frozen'):
        return finish('stop', 'frozen')
    if policy.get('approved_by') != 'demo-owner':
        return finish('stop', 'owner_approval_missing')
    if payload['notificationId'] not in policy.get('allowed_notification_ids', []):
        return finish('stop', 'out_of_scope')
    try:
        observation = http(base, '/receipt')
    except (OSError, TimeoutError, ValueError) as exc:
        audit.append({'query_error': type(exc).__name__})
        return finish('unknown', 'receipt_query_failed')
    audit.append({'query': '/receipt', 'response': observation})
    body = observation.get('body') or {}
    if observation['http_status'] != 200:
        return finish('unknown', 'receipt_query_failed')
    if (body.get('source') != 'receiver' or body.get('notification_id') != payload['notificationId']
            or body.get('order_id') != payload['orderId'] or body.get('request_id') != payload['requestId']):
        return finish('stop', 'evidence_identity_mismatch')
    if body.get('status') == 'completed':
        receipt = body.get('receipt') or {}
        if receipt != payload:
            return finish('stop', 'receipt_payload_mismatch')
        return finish('already_completed', 'do_not_repeat_effect')
    if body.get('status') != 'not_completed' or body.get('attempt_closed') is not True:
        return finish('unknown', 'no_terminal_negative_evidence')
    if state.get('attempts', 0) >= policy.get('max_recovery_attempts', 0):
        return finish('stop', 'recovery_budget_exhausted')
    state['attempts'] = state.get('attempts', 0) + 1
    try:
        applied = http(base, '/notify', payload)
        audit.append({'apply': '/notify', 'response': applied})
        if applied['http_status'] != 200:
            return finish('stop', 'receiver_rejected_retry')
        post = http(base, '/receipt')
        audit.append({'postcheck': '/receipt', 'response': post})
        if post['http_status'] != 200 or post.get('body', {}).get('receipt') != payload:
            return finish('unknown', 'postcheck_not_confirmed')
        return finish('recovered', 'same_event_confirmed_at_receiver')
    except (OSError, TimeoutError, ValueError) as exc:
        audit.append({'apply_error': type(exc).__name__})
        return finish('unknown', 'retry_outcome_not_confirmed')
