import {readFile, writeFile, mkdir, rename, realpath} from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {randomUUID} from 'node:crypto';
import {assert} from './contracts.mjs';
import {resolvePython} from './python-runtime.mjs';
export const PLUGINS = ['macro','industry','company','strategy','pdf'];
export async function readJSON(file, fallback) {
  try { return JSON.parse(await readFile(file, 'utf8')); }
  catch (error) { if (error.code === 'ENOENT' && fallback !== undefined) return fallback; throw error; }
}
export async function writeJSON(file, value) {
  await mkdir(path.dirname(file), {recursive:true});
  const temp = `${file}.${randomUUID()}.tmp`;
  await writeFile(temp, JSON.stringify(value, null, 2), 'utf8'); await rename(temp, file);
}
export async function installPackage(root, pkg) {
  assert(pkg && pkg.package_version === '1.0' && PLUGINS.includes(pkg.module), 'Gói cần package_version=1.0 và module hợp lệ.');
  assert(typeof pkg.entrypoint === 'string' && /\.(mjs|py)$/.test(pkg.entrypoint), 'Entrypoint chỉ nhận .mjs hoặc .py.');
  assert(Array.isArray(pkg.files) && pkg.files.length > 0 && pkg.files.length <= 100, 'Gói cần 1–100 file.');
  const files = new Set(); let bytes = 0;
  for (const file of pkg.files) {
    assert(file && typeof file.path === 'string' && typeof file.content === 'string', 'File cần path và content dạng chuỗi.');
    assert(!file.path.includes('\\') && !file.path.includes(':') && !file.path.startsWith('/') && file.path.split('/').every(part => /^[A-Za-z0-9_.-]+$/.test(part) && !['.','..'].includes(part)), 'Đường dẫn file không an toàn.');
    assert(/\.(py|mjs|js|json|txt|md|css|html)$/.test(file.path) && !file.path.split('/').some(part => part.startsWith('.')), 'Chỉ nhận mã nguồn/text; không nhận file ẩn hoặc binary.');
    assert(!files.has(file.path), 'Trùng file trong gói.'); files.add(file.path);
    bytes += Buffer.byteLength(file.content); assert(bytes <= 8 * 1024 * 1024, 'Gói module vượt 8 MB.');
  }
  assert(files.has(pkg.entrypoint), 'Entrypoint không có trong files.');
  const version = randomUUID(), base = path.join(root, pkg.module, 'versions', version);
  for (const file of pkg.files) { const target = path.join(base, file.path); await mkdir(path.dirname(target), {recursive:true}); await writeFile(target, file.content, 'utf8'); }
  const registryPath = path.join(root, 'registry.json'), registry = await readJSON(registryPath, {});
  registry[pkg.module] = {version, entrypoint: pkg.entrypoint, installed_at:new Date().toISOString()};
  await writeJSON(registryPath, registry);
  return registry;
}
export async function executeModule(root, name, input) {
  const registry = await readJSON(path.join(root,'registry.json'), {}), config = registry[name];
  assert(config, `Chưa cài module ${name}.`);
  const base = path.join(root, name, 'versions', config.version), entry = path.join(base, config.entrypoint);
  const resolved = await realpath(entry), realBase = await realpath(base);
  assert(resolved.startsWith(`${realBase}${path.sep}`), 'Entrypoint nằm ngoài thư mục module.');
  const isPython = config.entrypoint.endsWith('.py');
  const executable = isPython ? await resolvePython() : process.execPath;
  const args = isPython ? ['-X','utf8',resolved] : [resolved];
  return new Promise((resolve, reject) => {
    const child = spawn(executable, args, {cwd:base, shell:false, windowsHide:true, stdio:['pipe','pipe','pipe'], env:{...process.env,PYTHONIOENCODING:'utf-8'}});
    const stdoutChunks=[]; let size=0, settled=false;
    const finish = (error, result) => { if (settled) return; settled=true; clearTimeout(timer); error ? reject(error) : resolve(result); };
    const timer = setTimeout(() => { child.kill(); finish(new Error(`${name}: vượt thời gian 120 giây.`)); },120_000);
    child.stdout.on('data', chunk => { size+=chunk.length; if(size>10*1024*1024) {child.kill();finish(new Error(`${name}: output vượt 10 MB.`));} else stdoutChunks.push(chunk); });
    // Drain diagnostic output without exposing it as an HTTP response.
    child.stderr.on('data', () => {});
    child.on('error', e => finish(new Error(`${name}: không khởi chạy được ${isPython?'Python (kiểm tra PYTHON_BIN)':'Node.js'}: ${e.code || e.message}.`)));
    child.on('close', code => { if(code!==0)return finish(new Error(`${name}: chương trình kết thúc với mã ${code}; kiểm tra module bằng lệnh bàn giao.`)); try {finish(null,JSON.parse(Buffer.concat(stdoutChunks).toString('utf8').replace(/^\uFEFF/, '').trim()));} catch {finish(new Error(`${name}: stdout phải chứa đúng một JSON; chuyển log sang stderr.`));} });
    child.stdin.on('error', () => {}); child.stdin.end(JSON.stringify(input));
  });
}
