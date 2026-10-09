import test from 'node:test';
import assert from 'node:assert/strict';
import {buildDashboardData,dashboardMarkup} from '../public/dashboard.js';
import {validateRequest} from '../lib/contracts.mjs';

const request={ticker:'TST',exchange:'HOSE',period_start:'2025-01-01',period_end:'2025-03-31',as_of_date:'2025-03-31',investment_horizon:'Software test',financial_basis:'annual',statement_scope:'consolidated'};
function fixture() {
  const prices=Array.from({length:25},(_,i)=>({date:new Date(Date.UTC(2025,0,i+1)).toISOString().slice(0,10),close:i+1,volume:i===0?0:null,adjustment_basis:'software_test_only'}));
  return {request,modules:{company:{data:{price_series:prices,financials:[]},sources:[]}}};
}
test('MA20 uses only prior 20 observations, preserves missing prices, filters cutoff and handles zero',()=>{
  const a=fixture();
  a.modules.company.data.price_series.push({date:'2026-01-01',close:999,volume:999});
  let d=buildDashboardData(a);
  assert.equal(d.prices.length,25);assert.equal(d.prices[18].ma20,null);assert.equal(d.prices[19].ma20,10.5);
  assert.equal(d.prices[0].volume,0);assert.equal(d.prices[1].volume,null);
  a.modules.company.data.price_series[20].close=null;
  d=buildDashboardData(a);assert.equal(d.prices[20].ma20,null);assert.equal(d.prices[24].ma20,null);
  assert.ok(!dashboardMarkup(a).includes('NaN'));
  a.modules.company.data.price_series=[{date:'2025-01-01',close:0,volume:0}];
  d=buildDashboardData(a);assert.equal(d.summary.change,null);assert.equal(d.summary.low,0);
});
test('financial charts exclude YTD, other scopes and future publications; preserve negative CFO',()=>{
  const a=fixture(),company=a.modules.company;
  company.sources=[{source_id:'company:test',publication_date_verified:true,published_at:'2025-03-01'}];
  const row={item_id:'cfo',value:-100,unit:'VND',verified:true,frequency:'annual',statement_scope:'consolidated',period_start:'2024-01-01',period_end:'2024-12-31',source_refs:['company:test']};
  company.data.financials=[row,{...row,item_id:'revenue',value:1000},{...row,frequency:'ytd',value:999},{...row,statement_scope:'separate',value:999}];
  assert.equal(buildDashboardData(a).periods[0].values.cfo,-100);
  company.sources[0].published_at='2025-04-01';assert.equal(buildDashboardData(a).periods.length,0);
});
test('rolling range clamps month-end and markup escapes labels; industry input is optional',()=>{
  const a=fixture();
  a.request={...request,ticker:'<script>alert(1)</script>'};
  assert.ok(!dashboardMarkup(a).includes('<script>'));
  assert.ok(dashboardMarkup(a).includes('&lt;script&gt;'));
  const req=validateRequest({...request,ticker:'HPG'},'test-run');assert.equal(req.industry_code,'1750');
  assert.equal(validateRequest(request,'test-run').industry_code,'UNCLASSIFIED');
  a.modules.company.data.price_series=[{date:'2025-02-27',close:1,volume:1},{date:'2025-02-28',close:2,volume:2},{date:'2025-03-31',close:3,volume:3}];
  assert.equal(buildDashboardData(a,'m1').prices[0].date,'2025-02-28');
});
