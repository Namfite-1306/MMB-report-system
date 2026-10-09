import {copyFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {installPackage} from './plugins.mjs';

const source=fileURLToPath(new URL('../MMB_company_module_nguoi3/company/examples/hpg_raw/',import.meta.url));
// PDF evidence exceeds the text-package limit. Trusted local installation copies
// only these known evidence files; member 3 verifies their original SHA256.
export async function installTeamPackage(root,pkg) {
  const registry=await installPackage(root,pkg);
  if(pkg.module==='company') {
    const target=path.join(root,'company','versions',registry.company.version,'company','examples','hpg_raw');
    await mkdir(target,{recursive:true});
    for(const file of ['annual_pdf.pdf','interim_pdf.pdf','issuer_publication_page.html'])
      await copyFile(path.join(source,file),path.join(target,file));
  }
  return registry;
}
