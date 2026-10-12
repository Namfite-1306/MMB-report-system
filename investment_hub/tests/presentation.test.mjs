import test from 'node:test';
import assert from 'node:assert/strict';
import {metricPresentation,investorOverview,runLabel,matchesMetric} from '../public/presentation.js';

test('investor display formats units without changing original metrics or treating missing as zero',()=>{
  const metric={metric_id:'macro:vn_real_gdp_growth_annual_yoy_2024',value:.0709,unit:'ratio',period_start:'2024-01-01',period_end:'2024-12-31'};
  const original=structuredClone(metric),display=metricPresentation(metric);
  assert.equal(display.value,'7,09');assert.equal(display.unit,'%');assert.match(display.label,/GDP/);
  assert.deepEqual(metric,original);
  assert.equal(metricPresentation({...metric,value:0}).value,'0');
  assert.equal(metricPresentation({...metric,value:null}).value,'Chưa có');
  assert.equal(metricPresentation({...metric,value:-2e9,unit:'VND'}).value,'-2');
  assert.equal(metricPresentation({...metric,value:-2e9,unit:'VND'}).unit,'Tỷ VND');
  assert.equal(metricPresentation({...metric,value:1.185,unit:'x'}).unit,'Lần');
});
function snapshot(){
  return {request:{period_start:'2023-01-01',period_end:'2025-12-31',as_of_date:'2025-12-31',financial_basis:'quarterly',statement_scope:'consolidated'},conclusion_usable:false,
    modules:{macro:{status:'partial'},industry:{status:'partial'},strategy:{status:'partial',data:{rules:[{status:'insufficient_data'}]}},company:{status:'partial',sources:[{source_id:'s',publication_date_verified:true,published_at:'2025-03-01'}],data:{
      price_series:[{date:'2025-01-02',close:10,volume:0,adjustment_basis:'provider_adjusted_unspecified'}],
      financials:[{item_id:'revenue',value:100,verified:true,unit:'VND',frequency:'annual',statement_scope:'consolidated',period_start:'2024-01-01',period_end:'2024-12-31',source_refs:['s']}]}}}};
}
test('overview explains coverage and suggests only available same-scope annual data before cutoff',()=>{
  const a=snapshot(),overview=investorOverview(a);
  assert.equal(overview.gap,true);assert.equal(overview.annualAvailable,true);assert.equal(overview.data.periods.length,0);
  assert.match(overview.reasons.join(' '),/Quý/);assert.match(overview.reasons.join(' '),/điều chỉnh/);
  a.modules.company.sources[0].published_at='2026-01-01';assert.equal(investorOverview(a).annualAvailable,false);
  a.modules.company.sources[0].published_at='2025-03-01';a.request.statement_scope='separate';assert.equal(investorOverview(a).annualAvailable,false);
});
test('overview distinguishes execution failures from pending and small calendar gaps',()=>{
  const a=snapshot();a.request.period_start='2025-01-01';a.modules.company.status='error';a.modules.strategy.status='pending';
  const overview=investorOverview(a);
  assert.equal(overview.gap,false);assert.deepEqual(overview.blocked,['Doanh nghiệp']);assert.deepEqual(overview.pending,['Chiến lược']);
  assert.match(overview.reasons[0],/lỗi/);
});
test('metric search supports Vietnamese without accents and keeps zero separate from missing',()=>{
  const m={metric_id:'company:net_profit',name:'Lợi nhuận sau thuế',value:0,unit:'VND',period_start:'2025-01-01',period_end:'2025-12-31'};
  assert.equal(matchesMetric(m,'company',{query:'loi nhuan 2025'}),true);
  assert.equal(matchesMetric(m,'company',{section:'macro'}),false);
  assert.equal(matchesMetric(m,'company',{missingOnly:true}),false);
  assert.equal(matchesMetric({...m,value:null},'company',{query:'thuế',missingOnly:true}),true);
  assert.equal(matchesMetric(m,'company',{query:'doanh thu'}),false);
});
test('saved run labels distinguish frequency and scope without exposing full UUID',()=>{
  const r={ticker:'HPG',as_of_date:'2026-10-09',financial_basis:'quarterly',statement_scope:'separate',run_id:'abcdef12-3456-7890-1234-123456789012'};
  assert.equal(runLabel(r),'HPG · 09/10/2026 · Quý · Riêng lẻ · abcdef12');
  assert.match(runLabel({...r,financial_basis:'annual',statement_scope:'consolidated'}),/Năm · Hợp nhất/);
});
