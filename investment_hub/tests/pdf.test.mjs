import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';
import {createApp} from '../server.mjs';
import {installPackage} from '../lib/plugins.mjs';
import {resolvePython} from '../lib/python-runtime.mjs';

const source = fileURLToPath(new URL('../PDF Format/report/',import.meta.url));
const python = await resolvePython();
const probe = spawnSync(python,['-c','import reportlab,pypdf'],{windowsHide:true});
const ready = !probe.error && probe.status === 0;
const skip = ready ? false : 'Python với ReportLab/pypdf chưa có; xem PDF Format/report/requirements.txt.';

test('PDF renderer blocks unsafe raw conclusion, wraps long tables and preserves numbers', {skip}, () => {
  const result = spawnSync(python,['-X','utf8','-m','unittest','discover','-s',path.join(source,'tests'),'-v'],
    {encoding:'utf8',windowsHide:true,timeout:30000});
  assert.equal(result.status,0,result.stderr || result.error?.message);
});

test('member 6 Python package exports real Vietnamese PDF through the hub API', {skip}, async t => {
  const root = await mkdtemp(path.join(os.tmpdir(),'hub-real-pdf-'));
  const server = await createApp({root});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  t.after(async()=>{await new Promise(resolve=>server.close(resolve));await rm(root,{recursive:true,force:true});});
  const files = [];
  for(const name of ['run.py','src/pdf_generator.py','src/dashboard.py']) files.push({path:name,content:await readFile(path.join(source,name),'utf8')});
  await installPackage(path.join(root,'modules'),{package_version:'1.0',module:'pdf',entrypoint:'run.py',files});
  const base = `http://127.0.0.1:${server.address().port}`;
  async function post(route,body){const response=await fetch(base+route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return {status:response.status,data:await response.json()};}
  const created = await post('/api/runs',{ticker:'TST',exchange:'HOSE',industry_code:'TEST',
    industry_name:'KIỂM THỬ PHẦN MỀM, không phải dữ liệu đầu tư',as_of_date:'2026-10-09',
    period_start:'2025-01-01',period_end:'2025-12-31',investment_horizon:'Test only'});
  assert.equal(created.status,201);
  const id=created.data.analysis.run_id;
  const result=await post(`/api/runs/${id}/pdf`,{confirm_execution:true});
  assert.equal(result.status,200,JSON.stringify(result.data));
  assert.equal(result.data.manifest.conclusion_label,'insufficient_data');
  assert.ok(result.data.manifest.sections_present.includes('sources'));
  const response=await fetch(`${base}/api/runs/${id}/download/report.pdf`);
  assert.equal(response.status,200);
  const bytes=Buffer.from(await response.arrayBuffer());
  assert.ok(bytes.length>10000);assert.equal(bytes.subarray(0,5).toString(),'%PDF-');
  const run=(await (await fetch(`${base}/api/runs/${id}`)).json());
  assert.equal(run.pdf_available,true);
  const downloaded=(await (await fetch(`${base}/api/runs/${id}/download/report_manifest.json`)).json());
  assert.equal(downloaded.run_id,id);
  await post(`/api/runs/${id}/upload`,{module:'industry',payload:created.data.analysis.modules.industry});
  assert.equal((await (await fetch(`${base}/api/runs/${id}`)).json()).pdf_available,false);
});
