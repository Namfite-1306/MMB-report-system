import {readFile,readdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
const [module,directory,entrypoint,output]=process.argv.slice(2);
if(!['macro','industry','company','strategy','pdf'].includes(module)||!directory||!entrypoint||!output){console.error('node scripts/package-module.mjs <module> <folder> <run.py|run.mjs> <output.module.json>');process.exit(1);}
const base=path.resolve(directory),files=[];
async function walk(dir){for(const item of await readdir(dir,{withFileTypes:true})){if(item.name.startsWith('.')||['node_modules','__pycache__','venv','storage'].includes(item.name))continue;const target=path.join(dir,item.name);if(item.isDirectory())await walk(target);else if(item.isFile()&&/\.(py|mjs|js|json|txt|md|css|html)$/.test(item.name)){if(path.resolve(target)===path.resolve(output))continue;files.push({path:path.relative(base,target).split(path.sep).join('/'),content:await readFile(target,'utf8')});}}}
await walk(base);if(!files.some(f=>f.path===entrypoint))throw Error('Entrypoint không tồn tại trong thư mục.');
await writeFile(output,JSON.stringify({package_version:'1.0',module,entrypoint,files},null,2),'utf8');console.log(`Đã đóng gói ${module}: ${files.length} file → ${output}`);
