import http from 'k6/http';
import {check} from 'k6';
import {Trend} from 'k6/metrics';
import exec from 'k6/execution';
const base=__ENV.BASE_URL, run=__ENV.RUN_ID;
const cancelMs=new Trend('cancel_ms',true);
export const options={scenarios:{first:{executor:'constant-arrival-rate',rate:10,timeUnit:'1s',duration:'20s',preAllocatedVUs:10,maxVUs:50}},systemTags:['status','method','name','scenario','check','error','error_code','expected_response'],summaryTrendStats:['avg','min','max','p(95)','p(99)'],thresholds:{checks:['rate==1'],http_req_failed:['rate==0'],cancel_ms:['p(95)<250'],dropped_iterations:['count==0']}};
function params(name){return {headers:{'Content-Type':'application/json','X-Actor':'teaching-test','X-Run-Id':run},tags:{name}};}
export function setup(){
 for(let i=0;i<210;i++){
  const r=http.post(base+'/orders',JSON.stringify({id:run+'-'+i,paid:true,shipped:false}),params('seed'));
  if(!check(r,{'seed succeeds':r=>r.status===200}))throw new Error('seed failed');
 }
}
export default function(){
 const i=exec.scenario.iterationInTest;
 if(i>=210)throw new Error('seed range exceeded');
 const r=http.post(base+'/orders/'+run+'-'+i+'/cancel',null,params('first cancel'));
 cancelMs.add(r.timings.duration);
 let b=null;try{b=r.json();}catch(e){}
 check(r,{'status 200':r=>r.status===200,'transitioned':()=>b&&b.transitioned===true,'refund flag':()=>b&&b.refund_requested===true,'notification id':()=>b&&typeof b.notification_id==='string'&&b.notification_id.length>0});
}
