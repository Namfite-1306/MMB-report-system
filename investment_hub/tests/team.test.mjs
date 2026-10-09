import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,mkdtemp,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {createApp} from '../server.mjs';
import {installTeamPackage} from '../lib/team-packages.mjs';

test('all member packages run with a common request and export HPG PDF without fabricated missing inputs', async t=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'hub-team-'));
  for(const name of ['macro','industry','company','strategy','pdf']) {
    const pkg=JSON.parse(await readFile(new URL(`../packages/${name}.module.json`,import.meta.url),'utf8'));
    await installTeamPackage(path.join(root,'modules'),pkg);
  }
  const server=await createApp({root});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  t.after(async()=>{await new Promise(resolve=>server.close(resolve));await rm(root,{recursive:true,force:true});});
  const base=`http://127.0.0.1:${server.address().port}`;
  async function post(route,body) {
    const response=await fetch(base+route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const result=await response.json();assert.ok(response.ok,JSON.stringify(result));return result;
  }
  const created=await post('/api/runs',{ticker:'HPG',exchange:'HOSE',
    as_of_date:'2026-10-09',period_start:'2025-01-01',period_end:'2026-10-08',investment_horizon:'Trung hạn',
    investment_horizon_months:12,financial_basis:'annual',statement_scope:'consolidated'});
  const id=created.analysis.run_id;
  assert.equal(created.analysis.request.industry_code,'1750');
  assert.equal(created.analysis.request.industry_name,'Sản xuất Thép & Kim loại');
  const result=await post(`/api/runs/${id}/pipeline`,{confirm_execution:true});
  assert.equal(result.execution.length,4);
  assert.ok(result.execution.every(e=>e.status==='saved'),JSON.stringify(result.execution));
  const analysis=result.analysis;
  for(const name of ['macro','industry','company','strategy']) {
    assert.equal(analysis.modules[name].run_id,id);
    assert.notEqual(analysis.modules[name].status,'error',JSON.stringify(analysis.modules[name].errors));
  }
  assert.ok(analysis.modules.company.data.financials.length>50);
  assert.ok(analysis.modules.company.data.price_series.length>100);
  assert.ok(analysis.modules.macro.data.metrics.some(m=>m.value===0.0709));
  assert.equal(analysis.modules.strategy.data.rules.length,9);
  assert.equal(analysis.modules.strategy.data.rules.find(r=>r.id==='fundamental').status,'evaluated');
  assert.equal(analysis.modules.strategy.data.rules.find(r=>r.id==='momentum').status,'insufficient_data');
  assert.equal(analysis.conclusion_usable,false);
  assert.deepEqual(analysis.errors,[]);
  const pdf=await post(`/api/runs/${id}/pdf`,{confirm_execution:true});
  assert.equal(pdf.manifest.run_id,id);
  const download=await fetch(`${base}/api/runs/${id}/download/report.pdf`);
  assert.equal(Buffer.from(await download.arrayBuffer()).subarray(0,5).toString(),'%PDF-');
  // A historical cutoff must filter later financial records and avoid future peer valuation.
  const historical=await post('/api/runs',{...created.analysis.request,as_of_date:'2025-01-06',period_start:'2024-01-01',period_end:'2025-01-06'});
  const old=await post(`/api/runs/${historical.analysis.run_id}/pipeline`,{confirm_execution:true});
  assert.ok(old.execution.every(e=>e.status==='saved'),JSON.stringify(old.execution));
  assert.ok(old.analysis.modules.industry.data.metrics.every(m=>m.period_end<='2025-01-06'));
  assert.ok(old.analysis.modules.company.data.financials.every(m=>m.period_end<='2025-01-06'));
  assert.equal(old.analysis.conclusion_usable,false);
  // Missing quarterly/TTM/separate observations can have null native periods.
  // They must not crash the adapter or acquire invented observation dates.
  for(const options of [
    {financial_basis:'quarterly',statement_scope:'consolidated'},
    {financial_basis:'ttm',statement_scope:'consolidated'},
    {financial_basis:'annual',statement_scope:'separate'}
  ]) {
    const missing=await post('/api/runs',{ticker:'HPG',exchange:'HOSE',industry_name:'Ngành',
      as_of_date:'2025-12-31',period_start:'2023-01-01',period_end:'2025-12-31',
      investment_horizon:'Ngắn hạn',investment_horizon_months:12,...options});
    const replay=await post(`/api/runs/${missing.analysis.run_id}/pipeline`,{confirm_execution:true});
    assert.ok(replay.execution.every(e=>e.status==='saved'),JSON.stringify(replay.execution));
    assert.deepEqual(replay.analysis.errors,[]);
    const company=replay.analysis.modules.company;
    assert.equal(company.status,'partial');
    assert.ok(company.data.price_series.length>100);
    const undated=company.native_output.data.metrics.filter(m=>m.period_start===null || m.period_end===null);
    assert.ok(undated.length>0);
    assert.ok(undated.every(m=>m.value===null));
    assert.ok(company.data.metrics.every(m=>m.period_start && m.period_end));
    assert.ok(company.warnings.some(w=>w.includes('chưa xác định kỳ')));
    assert.equal(replay.analysis.conclusion_usable,false);
    const report=await post(`/api/runs/${missing.analysis.run_id}/pdf`,{confirm_execution:true});
    assert.equal(report.manifest.overall_status,'partial');
  }
});
