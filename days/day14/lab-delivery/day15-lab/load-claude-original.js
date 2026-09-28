import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';
import exec from 'k6/execution';

const PROFILE = __ENV.PROFILE;
const BASE_URL = (__ENV.BASE_URL || '').replace(/\/+$/, '');
const RUN_ID = __ENV.RUN_ID;

if (!BASE_URL) {
  throw new Error('BASE_URL is required');
}
if (!RUN_ID) {
  throw new Error('RUN_ID is required (used for unique order ids and notification reconciliation)');
}

// First cancellation only; the repeat cancel is not part of this trend.
const cancelMs = new Trend('cancel_ms', true);

function arrival(rate, duration, startTime) {
  return {
    executor: 'constant-arrival-rate',
    rate: rate,
    timeUnit: '1s',
    duration: duration,
    startTime: startTime,
    preAllocatedVUs: 10,
    maxVUs: 50,
    tags: { profile: PROFILE },
  };
}

const PROFILES = {
  smoke: {
    smoke: arrival(1, '20s', '0s'),
  },
  spike: {
    spike_warmup: arrival(2, '20s', '0s'),
    spike_peak: arrival(20, '30s', '20s'),
    spike_recovery: arrival(2, '20s', '50s'),
  },
  sustain: {
    sustain: arrival(10, '120s', '0s'),
  },
};

if (!PROFILE || !Object.prototype.hasOwnProperty.call(PROFILES, PROFILE)) {
  throw new Error('Unknown PROFILE: ' + PROFILE + ' (expected one of: ' + Object.keys(PROFILES).join(', ') + ')');
}

export const options = {
  scenarios: PROFILES[PROFILE],
  tags: { run_id: RUN_ID },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
  thresholds: {
    checks: ['rate==1'],
    http_req_failed: [
      'rate==0',
      { threshold: 'rate<0.05', abortOnFail: true, delayAbortEval: '10s' },
    ],
    cancel_ms: ['p(95)<250'],
    dropped_iterations: ['count==0'],
  },
};

function headers(requestId) {
  return {
    'Content-Type': 'application/json',
    'X-Actor': 'teaching-test',
    'X-Run-Id': RUN_ID,
    'X-Request-Id': requestId,
  };
}

// Invalid or empty JSON yields null so the related checks fail and are counted.
function parseJson(res) {
  try {
    const body = res.json();
    return body !== null && typeof body === 'object' ? body : null;
  } catch (e) {
    return null;
  }
}

export default function () {
  const id = `${RUN_ID}-${exec.scenario.name}-${__VU}-${__ITER}`;
  const orderUrl = `${BASE_URL}/orders/${encodeURIComponent(id)}`;

  const createRes = http.post(`${BASE_URL}/orders`, JSON.stringify({ id: id, paid: true, shipped: false }), {
    headers: headers(id + '-create'),
    tags: { name: 'POST /orders', op: 'create' },
  });
  const created = parseJson(createRes);
  const createOk = check(createRes, {
    'create: status 200': (r) => r.status === 200,
    'create: valid JSON body': () => created !== null,
    'create: id echoed': () => created !== null && created.id === id,
  });
  if (!createOk) {
    return;
  }

  const first = http.post(`${orderUrl}/cancel`, null, {
    headers: headers(id + '-cancel1'),
    tags: { name: 'POST /orders/{id}/cancel', op: 'cancel_first' },
  });
  cancelMs.add(first.timings.duration);
  const firstBody = parseJson(first);
  check(first, {
    'cancel#1: status 200': (r) => r.status === 200,
    'cancel#1: valid JSON body': () => firstBody !== null,
    'cancel#1: transitioned true': () => firstBody !== null && firstBody.transitioned === true,
    'cancel#1: refund_requested true': () => firstBody !== null && firstBody.refund_requested === true,
    'cancel#1: notification_id present': () => firstBody !== null && typeof firstBody.notification_id === 'string' && firstBody.notification_id.length > 0,
  });

  const second = http.post(`${orderUrl}/cancel`, null, {
    headers: headers(id + '-cancel2'),
    tags: { name: 'POST /orders/{id}/cancel', op: 'cancel_repeat' },
  });
  const secondBody = parseJson(second);
  check(second, {
    'cancel#2: status 200': (r) => r.status === 200,
    'cancel#2: valid JSON body': () => secondBody !== null,
    'cancel#2: transitioned false': () => secondBody !== null && secondBody.transitioned === false,
    'cancel#2: refund_requested false': () => secondBody !== null && secondBody.refund_requested === false,
    'cancel#2: notification_id null': () => secondBody !== null && secondBody.notification_id === null,
  });

  const getRes = http.get(orderUrl, {
    headers: headers(id + '-get'),
    tags: { name: 'GET /orders/{id}', op: 'get' },
  });
  const state = parseJson(getRes);
  check(getRes, {
    'get: status 200': (r) => r.status === 200,
    'get: valid JSON body': () => state !== null,
    'get: order.cancelled true': () => state !== null && state.order !== null && typeof state.order === 'object' && state.order.cancelled === true,
  });
}
