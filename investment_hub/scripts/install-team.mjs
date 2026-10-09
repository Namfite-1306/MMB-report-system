import {readFile,writeFile,mkdir,readdir,copyFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {installTeamPackage} from '../lib/team-packages.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const repo=path.resolve(process.argv[2] || path.join(root,'..'));
const company=path.join(root,'MMB_company_module_nguoi3');
const vendor=path.join(root,'integrations','vendor');
async function collect(base,sub='',filter=()=>true) {
  const files=[];
  for(const entry of await readdir(path.join(base,sub),{withFileTypes:true})) {
    if(entry.name.startsWith('.') || entry.name==='__pycache__' || entry.name==='tests')continue;
    const relative=path.posix.join(sub,entry.name);
    if(entry.isDirectory()) files.push(...await collect(base,relative,filter));
    else if(filter(relative))files.push(relative);
  }
  return files;
}
const selections={
  macro:{base:path.join(repo,'macro-module'),files:['macro_module/__init__.py','macro_module/core.py','data/verified_macro_data.json','config/industry_mapping.json']},
  industry:{base:repo,files:(await collect(path.join(repo,'industry'),'',f=>f.endsWith('.py'))).map(f=>'industry/'+f)},
  company:{base:company,files:[...(await collect(path.join(company,'company'),'',f=>f.endsWith('.py')&&!f.startsWith('examples/'))).map(f=>'company/'+f),
    'company/examples/hpg_verified.json',...(await collect(path.join(company,'company/examples/hpg_raw'),'',f=>f.endsWith('.json'))).map(f=>'company/examples/hpg_raw/'+f)]},
  strategy:{base:path.join(repo,'strategy_module'),files:['strategy_v2.py','strategy_rules_v2.json']}
};
await mkdir(path.join(root,'packages'),{recursive:true});
for(const [module,selection] of Object.entries(selections)) {
  const files=[{path:'run.py',content:await readFile(path.join(root,'integrations','run.py'),'utf8')},
    {path:'adapter_config.json',content:JSON.stringify({module})}];
  for(const relative of selection.files){
    const source=path.join(selection.base,relative), target=path.join(vendor,module,relative);
    await mkdir(path.dirname(target),{recursive:true}); await copyFile(source,target);
    files.push({path:relative,content:await readFile(source,'utf8')});
  }
  const pkg={package_version:'1.0',module,entrypoint:'run.py',files};
  await writeFile(path.join(root,'packages',`${module}.module.json`),JSON.stringify(pkg,null,2),'utf8');
  await installTeamPackage(path.join(root,'modules'),pkg);
  console.log(`Đã cài ${module}: ${files.length} file; giữ nguyên bản bàn giao trong integrations/vendor.`);
}
