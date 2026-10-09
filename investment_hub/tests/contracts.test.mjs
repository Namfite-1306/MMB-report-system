import test from 'node:test';
import assert from 'node:assert/strict';
import {validateRequest,validateEnvelope,pending,assemble} from '../lib/contracts.mjs';
import {renderReport} from '../lib/report.mjs';
// These fixtures test software contracts only; they are not market observations.
export const request=validateRequest({ticker:'TST',exchange:'HOSE',industry_code:'TEST',industry_name:'Test fixture',as_of_date:'2026-10-09',period_start:'2025-01-01',period_end:'2025-12-31',investment_horizon:'Test horizon'},'00000000-0000-4000-8000-000000000001');
export function complete(module) {
  const e=pending(request,module);e.status='ok';e.warnings=[];
  e.sources=[{source_id:`${module}:source`,title:'Synthetic unit-test source',url:'https://example.test/fixture',published_at:'2026-01-01',retrieved_at:'2026-10-09T00:00:00Z',locator:null,publication_date_verified:true}];
  if(module==='strategy'){e.data.theory_sources=['Synthetic theory fixture'];e.data.rules=[{rule_id:'test'}];e.data.evidence_refs=['company:metric'];e.data.conclusion={label:'watchlist',rationale:'Synthetic assertion for validation only',evidence_refs:['company:metric'],horizon:request.investment_horizon};}
  else e.data.metrics=[{metric_id:`${module}:metric`,value:0,unit:'ratio',frequency:'annual',period_start:'2025-01-01',period_end:'2025-12-31',source_refs:[`${module}:source`],formula_id:null}];
  return e;
}
const all=()=>Object.fromEntries(['macro','industry','company','strategy'].map(k=>[k,complete(k)]));
test('input rejects invalid calendar dates and reversed periods',()=>{assert.throws(()=>validateRequest({...request,as_of_date:'2026-02-30'},request.run_id));assert.throws(()=>validateRequest({...request,period_start:'2026-01-01'},request.run_id));});
test('envelope refuses another run, ticker, schema or cutoff',()=>{for(const key of ['run_id','ticker','schema_version','as_of_date'])assert.throws(()=>validateEnvelope({...complete('company'),[key]:'different'},request,'company'));});
test('numbers remain numeric; zero is valid and missing is not zero',()=>{const e=complete('company');assert.doesNotThrow(()=>validateEnvelope(e,request,'company'));e.data.metrics[0].value='0%';assert.throws(()=>validateEnvelope(e,request,'company'));e.data.metrics[0].value=null;const modules=all();modules.company=e;assert.equal(assemble(request,modules).display_conclusion.label,'insufficient_data');});
test('broken source references and future periods are rejected',()=>{const e=complete('company');e.data.metrics[0].source_refs=['missing'];assert.throws(()=>validateEnvelope(e,request,'company'));e.data.metrics[0].source_refs=['company:source'];e.data.metrics[0].period_end='2027-01-01';assert.throws(()=>validateEnvelope(e,request,'company'));});
test('verified same-cutoff data permits conclusion; pending blocks it',()=>{const modules=all();assert.equal(assemble(request,modules).conclusion_usable,true);modules.macro=pending(request,'macro');const result=assemble(request,modules);assert.equal(result.conclusion_usable,false);assert.notEqual(result.overall_status,'ok');});
test('future or unknown publication cannot support investment conclusion',()=>{for(const source of [{published_at:'2027-01-01',publication_date_verified:true},{published_at:null,publication_date_verified:false}]){const modules=all();Object.assign(modules.company.sources[0],source);const a=assemble(request,modules);assert.equal(a.display_conclusion.label,'insufficient_data');assert.equal(a.modules.strategy.data.conclusion.label,'watchlist');}});
test('strategy evidence cannot refer to absent metric',()=>{const modules=all();modules.strategy.data.conclusion.evidence_refs=['company:absent'];assert.equal(assemble(request,modules).overall_status,'error');});
test('report escapes uploaded HTML',()=>{const modules=all();modules.company.data.findings=[{text:'<script>alert(1)</script>',evidence_refs:['company:metric']}];const html=renderReport(assemble(request,modules));assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('<script>alert'));});
