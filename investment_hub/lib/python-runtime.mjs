import {access} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

// Prefer an explicit team environment; the bundled runtime avoids WindowsApps aliases.
export async function resolvePython() {
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN;
  const bundled = path.join(os.homedir(), '.cache', 'codex-runtimes', 'codex-primary-runtime',
    'dependencies', 'python', process.platform === 'win32' ? 'python.exe' : 'bin/python3');
  try { await access(bundled); return bundled; } catch { return process.platform === 'win32' ? 'python' : 'python3'; }
}
