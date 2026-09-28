import http from 'k6/http';
import exec from 'k6/execution';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';
const cancelMs = new Trend('cancel_ms', true);
export const options = {
 stages: [{duration:'5s',target:1},{duration:'5s',target:5},{duration:'5s',target:10},{duration:'3s',target:0}],
 thresholds: {checks:['rate==1'],http_req_failed:['rate==0'],cancel_ms:['p(95)<250']},
};
export default function () {
 const id = `load-${__VU}-${__ITER}`;
 const url = __ENV.BASE_URL;
 const params = {headers:{'Content-Type':'application/json','X-Actor':'teaching-test','X-Request-Id':id,'X-Run-Id':__ENV.RUN_ID}};
 const created = http.post(`${url}/orders`,JSON.stringify({id,paid:true,shipped:false}),params);
 check(created, {'create succeeds':r=>r.status===200});
 const first = http.post(`${url}/orders/${id}/cancel`,null,params);
 const elapsed = exec.instance.currentTestRunDuration;
 const stage = elapsed < 5000 ? '0-1' : elapsed < 10000 ? '1-5' : elapsed < 15000 ? '5-10' : '10-0';
 cancelMs.add(first.timings.duration, {stage});
 check(first, {'first transitions and requests refund':r=>r.status===200&&r.json('transitioned')===true&&r.json('refund_requested')===true});
 const repeated = http.post(`${url}/orders/${id}/cancel`,null,params);
 check(repeated, {'repeat has no side effect':r=>r.status===200&&r.json('transitioned')===false&&r.json('refund_requested')===false&&r.json('notification_id')===null});
 const state = http.get(`${url}/orders/${id}`,params);
 check(state, {'state is cancelled':r=>r.status===200&&r.json('order.cancelled')===true});
 sleep(0.05);
}
