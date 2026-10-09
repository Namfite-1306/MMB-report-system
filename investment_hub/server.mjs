import http from 'node:http';
import {readFile, mkdir, readdir, realpath} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import {MODULES,DATA_MODULES,validateRequest,validateEnvelope,pending,assemble,assert} from './lib/contracts.mjs';
import {readJSON,writeJSON,installPackage,executeModule,PLUGINS} from './lib/plugins.mjs';
import {renderReport} from './lib/report.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
export async function createApp({root=here}={}) {
  const storage=path.join(root,'storage','runs'), plugins=path.join(root,'modules');
  await mkdir(storage,{recursive:true}); await mkdir(plugins,{recursive:true});
  const locks=new Set(); let installing=false;
  const runDir=id=>{assert(/^[a-f0-9-]{36}$/.test(id), 'run_id không hợp lệ.');return path.join(storage,id);};
  const getRun=async id=>{const dir=runDir(id);const meta=await readJSON(path.join(dir,'state.json'));const modules={};for(const name of MODULES)modules[name]=await readJSON(path.join(dir,`${name}.json`));return {dir,meta,request:meta.request,modules};};
  const saveAnalysis=async run=>{const analysis=assemble(run.request,run.modules);await writeJSON(path.join(run.dir,'analysis.json'),analysis);return analysis;};
  const commit=async(run,name,payload)=>{validateEnvelope(payload,run.request,name);await writeJSON(path.join(run.dir,`${name}.json`),payload);run.modules[name]=payload;
    if(DATA_MODULES.includes(name)){run.modules.strategy=pending(run.request,'strategy');run.modules.strategy.warnings=['Dữ liệu đã đổi. Cần chạy lại hoặc tải lên chiến lược mới.'];await writeJSON(path.join(run.dir,'strategy.json'),run.modules.strategy);}
    run.meta.revision++;run.meta.pdf=null;await writeJSON(path.join(run.dir,'state.json'),run.meta);};
  const json=(res,status,payload)=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(payload));};
  const body=async req=>{assert((req.headers['content-type']||'').startsWith('application/json'),'Yêu cầu cần Content-Type application/json.');let bytes=0;const chunks=[];for await(const chunk of req){bytes+=chunk.length;assert(bytes<=20*1024*1024,'Upload vượt 20 MB.');chunks.push(chunk);}try{return JSON.parse(Buffer.concat(chunks).toString('utf8'));}catch{throw new Error('JSON không hợp lệ.');}};
  const locked=async(id,action)=>{assert(!locks.has(id),'Lần phân tích đang xử lý, vui lòng đợi.');locks.add(id);try{return await action();}finally{locks.delete(id);}};
  const server=http.createServer(async(req,res)=>{
    try {
      const host=req.headers.host||'';assert(/^(localhost|127\.0\.0\.1):\d+$/.test(host),'Chỉ dùng host localhost hoặc 127.0.0.1.');
      const url=new URL(req.url,`http://${host}`), route=url.pathname;
      if(req.headers.origin)assert(req.headers.origin===`http://${host}`,'Không cho phép yêu cầu từ website khác.');
      res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('X-Frame-Options','DENY');
      if(req.method==='GET' && ['/','/app.js','/style.css','/dashboard.js','/dashboard.css'].includes(route)) {
        const file=route==='/'?'index.html':route.slice(1);res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript; charset=utf-8':'text/css; charset=utf-8');res.end(await readFile(path.join(here,'public',file)));return;
      }
      if(req.method==='GET'&&route==='/api/modules')return json(res,200,{registry:await readJSON(path.join(plugins,'registry.json'),{}),python_configured:!!process.env.PYTHON_BIN});
      if(req.method==='POST'&&route==='/api/modules/install') {
        const b=await body(req);assert(b.trusted===true,'Cần xác nhận gói mã nguồn do nhóm tin cậy.');assert(!installing,'Đang cài module khác.');installing=true;
        try{return json(res,200,{registry:await installPackage(plugins,b.package)});}finally{installing=false;}
      }
      if(route==='/api/runs'&&req.method==='GET') {
        const runs=[];for(const id of await readdir(storage)){try{const r=await readJSON(path.join(runDir(id),'state.json'));runs.push(r.request);}catch{}}
        return json(res,200,{runs:runs.reverse()});
      }
      if(route==='/api/runs'&&req.method==='POST') {
        const request=validateRequest(await body(req),randomUUID()),dir=runDir(request.run_id);await mkdir(dir);
        const run={dir,request,meta:{request,revision:0,pdf:null},modules:{}};
        await writeJSON(path.join(dir,'state.json'),run.meta);await writeJSON(path.join(dir,'request.json'),request);
        for(const name of MODULES){run.modules[name]=pending(request,name);await writeJSON(path.join(dir,`${name}.json`),run.modules[name]);}
        return json(res,201,{analysis:await saveAnalysis(run)});
      }
      const match=route.match(/^\/api\/runs\/([a-f0-9-]{36})(?:\/(.*))?$/);
      if(match){const [,id,action]=match;
        if(req.method==='GET'&&!action){const run=await getRun(id);return json(res,200,{analysis:assemble(run.request,run.modules),revision:run.meta.revision,pdf_available:!!run.meta.pdf});}
        if(req.method==='GET'&&action==='report'){const run=await getRun(id);res.setHeader('Content-Type','text/html; charset=utf-8');res.end(renderReport(assemble(run.request,run.modules)));return;}
        if(req.method==='GET'&&action?.startsWith('download/')){
          const run=await getRun(id),name=action.slice(9);let target;
          if(['request.json','analysis.json',...MODULES.map(k=>`${k}.json`)].includes(name)){if(name==='analysis.json')await saveAnalysis(run);target=path.join(run.dir,name);}
          else if(name==='report.pdf'||name==='report_manifest.json'){assert(run.meta.pdf,'Chưa có PDF từ module hoặc PDF đã cũ sau cập nhật dữ liệu.');target=path.join(run.dir,run.meta.pdf.directory,name);}
          else throw new Error('Tệp tải xuống không được hỗ trợ.');
          res.setHeader('Content-Type',name.endsWith('.pdf')?'application/pdf':'application/json; charset=utf-8');res.setHeader('Content-Disposition',`attachment; filename="${name}"`);res.end(await readFile(target));return;
        }
        if(req.method==='POST'&&action==='upload'){const b=await body(req);assert(MODULES.includes(b.module),'Module upload không hợp lệ.');return await locked(id,async()=>{const run=await getRun(id);await commit(run,b.module,b.payload);return json(res,200,{analysis:await saveAnalysis(run)});});}
        if(req.method==='POST'&&(action==='execute'||action==='pipeline')) {
          const b=await body(req);assert(b.confirm_execution===true,'Chỉ chạy module mã nguồn sau khi xác nhận.');
          const names=action==='pipeline'?MODULES:[b.module];assert(names.every(k=>MODULES.includes(k)),'Module không hợp lệ.');
          return await locked(id,async()=>{const run=await getRun(id),registry=await readJSON(path.join(plugins,'registry.json'),{}),execution=[];
            const execute=async name=>{if(!registry[name]){execution.push({module:name,status:'skipped',message:'Chưa cài module; giữ JSON hiện có.'});return;}try{const result=await executeModule(plugins,name,{request:run.request,modules:structuredClone(run.modules)});validateEnvelope(result,run.request,name);return {name,result};}catch(e){execution.push({module:name,status:'error',message:e.message});}};
            // Parallel data collection, then strategy reads the committed data snapshot.
            const results=await Promise.all(names.filter(k=>DATA_MODULES.includes(k)).map(execute));
            for(const result of results.filter(Boolean)){await commit(run,result.name,result.result);execution.push({module:result.name,status:'saved'});}
            if(names.includes('strategy')){const result=await execute('strategy');if(result){await commit(run,'strategy',result.result);execution.push({module:'strategy',status:'saved'});}}
            const analysis=await saveAnalysis(run);return json(res,200,{analysis,execution});
          });
        }
        if(req.method==='POST'&&action==='pdf') {
          const b=await body(req);assert(b.confirm_execution===true,'Cần xác nhận chạy module PDF.');
          return await locked(id,async()=>{const run=await getRun(id),analysis=await saveAnalysis(run),directory=`pdf-${run.meta.revision}-${randomUUID()}`,outputDir=path.join(run.dir,directory);await mkdir(outputDir);
            const result=await executeModule(plugins,'pdf',{analysis,output_dir:outputDir});
            assert(result.pdf_filename==='report.pdf'&&result.manifest,'PDF stdout cần {pdf_filename:"report.pdf", manifest:{...}}.');
            const manifest=result.manifest;
            for(const [key,value] of Object.entries({schema_version:'1.0',run_id:id,ticker:run.request.ticker,as_of_date:run.request.as_of_date,overall_status:analysis.overall_status,pdf_filename:'report.pdf'}))assert(manifest[key]===value,`PDF manifest.${key} không khớp.`);
            assert(typeof manifest.generated_at==='string'&&Number.isFinite(Date.parse(manifest.generated_at))&&Array.isArray(manifest.warnings),'PDF manifest thiếu generated_at/warnings.');
            assert(Array.isArray(manifest.sections_present)&&['macro','industry','company','strategy','risks','sources'].every(k=>manifest.sections_present.includes(k)),'PDF manifest phải có đủ các phần.');
            const filename=path.join(outputDir,'report.pdf'),real=await realpath(filename),realOut=await realpath(outputDir);assert(real.startsWith(realOut+path.sep),'PDF không được trỏ ra ngoài thư mục output.');
            const bytes=await readFile(filename);assert(bytes.length<=30*1024*1024&&bytes.subarray(0,5).toString()==='%PDF-'&&bytes.subarray(-1024).toString().includes('%%EOF'),'File output không có cấu trúc PDF hợp lệ.');
            await writeJSON(path.join(outputDir,'report_manifest.json'),manifest);run.meta.pdf={directory,revision:run.meta.revision};await writeJSON(path.join(run.dir,'state.json'),run.meta);
            return json(res,200,{pdf_available:true,manifest});
          });
        }
      }
      json(res,404,{error:'Không tìm thấy đường dẫn.'});
    } catch(error){if(!res.headersSent)json(res,error.code==='ENOENT'?404:400,{error:error.code==='ENOENT'?'Không tìm thấy tệp hoặc lần phân tích.':error.message});else res.end();}
  });
  return server;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const port=Number(process.env.PORT||3000);assert(Number.isInteger(port)&&port>0&&port<65536,'PORT không hợp lệ.');
  const server=await createApp();server.on('error',error=>{console.error(`Không mở máy chủ: ${error.message}`);process.exitCode=1;});
  server.listen(port,'127.0.0.1',()=>console.log(`MMB Analysis: http://127.0.0.1:${port}\nCtrl+C để dừng. JSON và module lưu trong investment_hub.`));
}
