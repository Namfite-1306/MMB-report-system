import test from 'node:test';
import assert from 'node:assert/strict';
import {requestJSON} from '../public/api.js';

test('network failures explain uncertain writes without retrying the action',async()=>{
  let attempts=0;
  const fail=async()=>{attempts++;throw new TypeError('network');};
  await assert.rejects(requestJSON('/api/runs',{ticker:'TST'},fail),/có thể đã được lưu/);
  assert.equal(attempts,1);
  await assert.rejects(requestJSON('/api/runs',undefined,fail),/Không kết nối được máy chủ/);
});
test('API errors preserve status for stale-run recovery and explain non-JSON responses',async()=>{
  await assert.rejects(requestJSON('/missing',undefined,async()=>({ok:false,status:404,json:async()=>({error:'Không tìm thấy'})})),e=>e.status===404 && e.message==='Không tìm thấy');
  await assert.rejects(requestJSON('/api/runs',undefined,async()=>({ok:false,status:502,json:async()=>{throw Error('html');}})),/HTTP 502/);
  assert.deepEqual(await requestJSON('/api/runs',undefined,async()=>({ok:true,status:200,json:async()=>({runs:[]})})),{runs:[]});
});
