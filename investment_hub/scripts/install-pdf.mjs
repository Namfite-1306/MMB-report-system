import {readFile, mkdir, writeFile} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {installPackage} from '../lib/plugins.mjs';
import {resolvePython} from '../lib/python-runtime.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const source = path.join(root, 'PDF Format', 'report');
const python = await resolvePython();
const probe = spawnSync(python, ['-X', 'utf8', '-c', 'from reportlab import Version; print(Version)'],
  {encoding:'utf8', windowsHide:true, timeout:15000});
if (probe.error || probe.status !== 0) {
  console.error('Python/ReportLab chưa sẵn sàng. Đặt PYTHON_BIN rồi cài PDF Format/report/requirements.txt.');
  console.error(probe.error?.message || probe.stderr); process.exit(1);
}
const files = [];
for (const filename of ['run.py','src/pdf_generator.py','src/dashboard.py','src/qa_checklist.py','requirements.txt']) {
  files.push({path:filename, content:await readFile(path.join(source, filename), 'utf8')});
}
const pkg = {package_version:'1.0', module:'pdf', entrypoint:'run.py', files};
const out = path.join(root, 'packages');
await mkdir(out, {recursive:true});
await writeFile(path.join(out, 'pdf.module.json'), JSON.stringify(pkg, null, 2), 'utf8');
await installPackage(path.join(root, 'modules'), pkg);
console.log('Đã đóng gói và cài PDF người 6. Runtime: ' + python + ' | ReportLab ' + probe.stdout.trim());
console.log('Khởi động lại web nếu server đang chạy từ phiên bản cũ, sau đó bấm Tạo PDF bằng module.');
