import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm,readFile} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {createApp} from '../server.mjs';
import {installPackage,executeModule} from '../lib/plugins.mjs';
import {pending} from '../lib/contracts.mjs';
const input={ticker:'TST',exchange:'HOSE',industry_code:'TEST',industry_name:'Synthetic software fixture',as_of_date:'2026-10-09',period_start:'2025-01-01',period_end:'2025-12-31',investment_horizon:'Test only'};
async function setup(t){const root=await mkdtemp(path.join(os.tmpdir(),'investment-hub-test-'));const server=await createApp({root});await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}`;t.after(async()=>{await new Promise(r=>server.close(r));await rm(root,{recursive:true,force:true});});const call=async(route,body)=>{const r=await fetch(base+route,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return {status:r.status,json:await r.json()};};return {root,base,call};}
test('create, persist, upload, download and invalidate old strategy',async t=>{
  const {call,base}=await setup(t);const created=await call('/api/runs',input);assert.equal(created.status,201);const id=created.json.analysis.run_id,request=created.json.analysis.request;
  assert.equal(created.json.analysis.overall_status,'pending');let strategy=pending(request,'strategy');strategy.warnings=['Test uploaded revision'];
  assert.equal((await call(`/api/runs/${id}/upload`,{module:'strategy',payload:strategy})).status,200);
  const macro=pending(request,'macro');let result=await call(`/api/runs/${id}/upload`,{module:'macro',payload:macro});assert.equal(result.status,200);assert.match(result.json.analysis.modules.strategy.warnings[0],/Dữ liệu đã đổi/);
  macro.ticker='OTHER';assert.equal((await call(`/api/runs/${id}/upload`,{module:'macro',payload:macro})).status,400);
  const requestFile=await fetch(`${base}/api/runs/${id}/download/request.json`);assert.equal((await requestFile.json()).run_id,id);
  assert.equal((await call(`/api/runs/${id}`)).json.analysis.run_id,id);assert.equal((await call('/api/runs')).json.runs.length,1);
  assert.equal((await fetch(`${base}/api/runs/${id}/report`)).status,200);assert.equal((await fetch(`${base}/api/runs/${id}/download/report.pdf`)).status,400);
});
test('uploads cannot install untrusted code or escape package directory',async t=>{const {call,root}=await setup(t);assert.equal((await call('/api/modules/install',{package:{}})).status,400);await assert.rejects(installPackage(path.join(root,'modules'),{package_version:'1.0',module:'strategy',entrypoint:'run.mjs',files:[{path:'../run.mjs',content:'x'}]}));});
test('installed JS module executes with stdin JSON and respects schema',async t=>{
  const {call}=await setup(t);const code=await readFile(new URL('../templates/run.mjs',import.meta.url),'utf8');const install=await call('/api/modules/install',{trusted:true,package:{package_version:'1.0',module:'strategy',entrypoint:'run.mjs',files:[{path:'run.mjs',content:code}]}});assert.equal(install.status,200);
  const created=await call('/api/runs',input),id=created.json.analysis.run_id;
  assert.equal((await call(`/api/runs/${id}/execute`,{module:'strategy'})).status,400);
  const result=await call(`/api/runs/${id}/execute`,{module:'strategy',confirm_execution:true});assert.equal(result.status,200);assert.equal(result.json.execution[0].status,'saved');assert.equal(result.json.analysis.modules.strategy.status,'pending');
  const pipeline=await call(`/api/runs/${id}/pipeline`,{confirm_execution:true});assert.equal(pipeline.status,200);assert.equal(pipeline.json.execution.filter(e=>e.status==='skipped').length,3);
});
test('failed runner keeps previous valid output and reports error',async t=>{const {call}=await setup(t);await call('/api/modules/install',{trusted:true,package:{package_version:'1.0',module:'macro',entrypoint:'run.mjs',files:[{path:'run.mjs',content:'console.log("not-json")'}]}});const created=await call('/api/runs',input),id=created.json.analysis.run_id;const r=await call(`/api/runs/${id}/execute`,{module:'macro',confirm_execution:true});assert.equal(r.json.execution[0].status,'error');assert.equal(r.json.analysis.modules.macro.status,'pending');});
test('reject cross-site API requests and arbitrary static paths',async t=>{const {base}=await setup(t);const r=await fetch(base+'/api/runs',{method:'POST',headers:{'Content-Type':'application/json',Origin:'https://example.test'},body:JSON.stringify(input)});assert.equal(r.status,400);assert.equal((await fetch(base+'/server.mjs')).status,404);});

test('runner preserves Vietnamese UTF-8 split across stdout chunks',async t=>{
  const {root}=await setup(t),modules=path.join(root,'modules');
  const code='const bytes=Buffer.from(JSON.stringify({label:"chiến lược"})); for(const byte of bytes){process.stdout.write(Buffer.from([byte]));await new Promise(r=>setTimeout(r,2));}';
  await installPackage(modules,{package_version:'1.0',module:'strategy',entrypoint:'run.mjs',files:[{path:'run.mjs',content:code}]});
  assert.equal((await executeModule(modules,'strategy',{})).label,'chiến lược');
});

test('PDF adapter validates manifest, downloads output and invalidates stale report',async t=>{
  const {call,base}=await setup(t);
  // Structural transport fixture only; this test does not certify PDF layout.
  const code=`import {writeFile} from 'node:fs/promises';import path from 'node:path';let raw='';for await(const chunk of process.stdin)raw+=chunk;const {analysis:a,output_dir}=JSON.parse(raw);await writeFile(path.join(output_dir,'report.pdf'),'%PDF-1.4\\n%%EOF\\n');console.log(JSON.stringify({pdf_filename:'report.pdf',manifest:{schema_version:'1.0',run_id:a.run_id,ticker:a.request.ticker,as_of_date:a.request.as_of_date,overall_status:a.overall_status,generated_at:new Date().toISOString(),warnings:a.warnings,sections_present:['macro','industry','company','strategy','risks','sources'],pdf_filename:'report.pdf'}}));`;
  const pkg={package_version:'1.0',module:'pdf',entrypoint:'run.mjs',files:[{path:'run.mjs',content:code}]};
  assert.equal((await call('/api/modules/install',{trusted:true,package:pkg})).status,200);
  const created=await call('/api/runs',input),id=created.json.analysis.run_id;
  assert.equal((await call(`/api/runs/${id}/pdf`,{confirm_execution:true})).status,200);
  const pdf=await fetch(`${base}/api/runs/${id}/download/report.pdf`);assert.equal(pdf.status,200);assert.match(await pdf.text(),/^%PDF/);
  assert.equal((await call(`/api/runs/${id}/download/report_manifest.json`)).json.run_id,id);
  await call(`/api/runs/${id}/upload`,{module:'macro',payload:pending(created.json.analysis.request,'macro')});
  assert.equal((await fetch(`${base}/api/runs/${id}/download/report.pdf`)).status,400);
  pkg.files[0].content=code.replace('run_id:a.run_id',"run_id:'incorrect'");
  await call('/api/modules/install',{trusted:true,package:pkg});
  assert.equal((await call(`/api/runs/${id}/pdf`,{confirm_execution:true})).status,400);
  assert.equal((await call(`/api/runs/${id}`)).json.pdf_available,false);
});
