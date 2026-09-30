// 上線前壓測：健康服務（無故障注入）逐步加壓，找 p95 跨過 250ms（後續 定的門檻）的那一點。
// 每次迭代建一張新訂單（唯一 id）再取消它，模擬持續進來的新取消請求，不是重複打同一張。
import http from 'k6/http';
import { check } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const API = __ENV.API_URL || 'http://127.0.0.1:5080';
const cancelLatency = new Trend('cancel_latency_ms', true);
const createFailures = new Counter('create_failures');
const cancelFailures = new Counter('cancel_failures');

export const options = {
  scenarios: {
    ramp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '20s', target: 10 },
        { duration: '20s', target: 25 },
        { duration: '20s', target: 50 },
        { duration: '20s', target: 100 },
        { duration: '20s', target: 200 },
        { duration: '20s', target: 400 },
        { duration: '10s', target: 0 },
      ],
      gracefulRampDown: '5s',
    },
  },
  thresholds: {
    // 後續 的門檻：p95 <= 250ms。不讓它中斷測試（abortOnFail: false），只記錄有沒有越界。
    'cancel_latency_ms': [{ threshold: 'p(95)<250', abortOnFail: false }],
  },
};

let seq = 0;

export default function () {
  const vu = __VU;
  const iter = __ITER;
  seq += 1;
  const id = `PL-${vu}-${iter}-${Date.now()}-${seq}`;

  const createRes = http.post(
    `${API}/orders`,
    JSON.stringify({ id, shipped: false, paid: true }),
    { headers: { 'Content-Type': 'application/json' } },
  );
  if (createRes.status !== 200) {
    createFailures.add(1);
    return;
  }

  const t0 = Date.now();
  const cancelRes = http.post(
    `${API}/orders/${id}/cancel`,
    null,
    { headers: { 'X-Actor': 'k6-prelaunch', 'X-Run-Id': `k6-${__ENV.K6_RUN_ID || 'local'}` } },
  );
  cancelLatency.add(Date.now() - t0);

  const ok = check(cancelRes, { 'cancel 200': (r) => r.status === 200 });
  if (!ok) cancelFailures.add(1);
}
