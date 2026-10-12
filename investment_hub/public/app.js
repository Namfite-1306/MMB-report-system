import {dashboardMarkup} from './dashboard.js';
import {metricPresentation,investorOverview,displayDate,RULE_NAMES,RULE_STATUS,runLabel,matchesMetric} from './presentation.js';
import {requestJSON} from './api.js';
const $ = id => document.getElementById(id);
const names = {macro:'Vĩ mô', industry:'Ngành', company:'Doanh nghiệp', strategy:'Chiến lược'};
const descriptions = {
  macro:'Người 1 · Chỉ số và tác động vĩ mô',
  industry:'Người 2 · Ngành, doanh nghiệp so sánh và triển vọng',
  company:'Người 3 · Giá, BCTC và chỉ số doanh nghiệp',
  strategy:'Người 4 · Lý thuyết đầu tư, quy tắc và kết luận'
};
const icons = {macro:'◎', industry:'▤', company:'◫', strategy:'↗'};
const statusNames = {pending:'Đang chờ', ok:'Đã nhận', partial:'Chưa hoàn chỉnh', error:'Có lỗi'};
const labels = {attractive:'Có cơ hội', watchlist:'Theo dõi', unattractive:'Chưa hấp dẫn', insufficient_data:'Chưa đủ dữ liệu'};
let analysis = null, registry = {}, busy = false, pdfAvailable = false;
let chartRange = 'all';
let busyText='';
let draftNote='';
function formRequest() {
  return Object.fromEntries(Array.from($('request-form').elements).filter(field=>field.name).map(field=>[field.name,field.value]));
}
const draftKey=()=> 'mmb-draft-'+(analysis?.run_id || 'new');
function saveDraft() {
  try {
    if(!draftChanged() && analysis){localStorage.removeItem(draftKey());draftNote='';}
    else {localStorage.setItem(draftKey(),JSON.stringify(formRequest()));draftNote='Bản nháp được lưu trên trình duyệt này; chưa áp dụng vào kết quả.';}
  } catch {draftNote='Không lưu được bản nháp trên trình duyệt này. Hãy tạo lần phân tích để lưu cấu hình vào hệ thống.';}
}
function restoreDraft() {
  draftNote='';
  try {
    const saved=JSON.parse(localStorage.getItem(draftKey()) || 'null');
    if(!saved || typeof saved!=='object')return;
    for(const field of Array.from($('request-form').elements))if(field.name && typeof saved[field.name]==='string')field.value=saved[field.name];
    draftNote='Đã khôi phục bản nháp trên trình duyệt này; kết quả vẫn thuộc cấu hình đã lưu.';
  } catch {draftNote='Không đọc được bản nháp; cấu hình đã lưu vẫn được giữ.';}
}
function draftChanged() {
  if(!analysis)return false;
  const draft=formRequest();
  return Object.entries(draft).some(([key,value])=>String(value).trim().toUpperCase()!==String(analysis.request[key] ?? '').trim().toUpperCase());
}
function renderDraftState() {
  const changed=draftChanged();
  $('form-feedback').textContent=changed?'Cấu hình đã đổi nhưng kết quả bên phải vẫn thuộc lần đã lưu. Bấm Tạo lần phân tích để áp dụng cấu hình mới.':'';
  $('draft-status').textContent=draftNote;
  $('draft-discard').hidden=!changed;
  availability($('draft-discard'),!!analysis && changed);
  availability($('pipeline'),!!analysis && !changed && Object.keys(names).some(k=>registry[k]),changed?'Tạo lần phân tích mới để áp dụng cấu hình.':'Tạo input và cài module trước.');
  availability($('pdf-generate'),!!analysis && !changed && !!registry.pdf);
  if($('use-annual'))availability($('use-annual'),!changed,'Tạo lần phân tích mới để áp dụng cấu hình đang sửa.');
  for(const button of document.querySelectorAll('[data-run-module]'))availability(button,!!analysis && !changed && !!registry[button.dataset.runModule]);
}
function rememberRun() { try{localStorage.setItem('mmb-last-run',analysis.run_id);}catch{} }
function syncForm() {
  for(const field of Array.from($('request-form').elements))if(field.name)field.value=analysis.request[field.name] ?? '';
}
async function openRun(id) {
  const result=await api('/api/runs/'+id);
  analysis=result.analysis;pdfAvailable=result.pdf_available;chartRange='all';$('execution').hidden=true;
  syncForm();restoreDraft();rememberRun();
}
async function createAnalysis(request) {
  if(request.period_start>request.period_end || request.period_end>request.as_of_date)throw Error('Cần Từ ngày ≤ Đến ngày ≤ Ngày chốt. Kiểm tra lại ba ngày trong thiết lập.');
  const previousDraft=draftKey();
  const result=await api('/api/runs',request);
  analysis=result.analysis;pdfAvailable=false;chartRange='all';$('execution').hidden=true;
  try{localStorage.removeItem(previousDraft);}catch{}draftNote='';
  syncForm();rememberRun();await loadRuns();
}
function renderOverview() {
  const host=$('investor-overview');host.replaceChildren();
  const overview=investorOverview(analysis);if(!overview)return;
  const grid=element('div','coverage-grid');
  const cards=[['Dữ liệu giá thực có',overview.pricePeriod,overview.data.summary.count+' phiên có giá · Kỳ yêu cầu '+displayDate(analysis.request.period_start)+' – '+displayDate(analysis.request.period_end)],
    ['BCTC đúng lựa chọn',overview.financialPeriod,overview.financialLabel+' · '+overview.data.periods.length+' kỳ đã xác minh'],
    ['Khả năng dùng kết luận',analysis.conclusion_usable?'Đủ điều kiện của hệ thống':'Chưa thể dùng kết luận',overview.pending.length?'Đang chờ xử lý':overview.missingRules+' trụ cột chiến lược thiếu đầu vào']];
  for(const [label,value,note] of cards){const card=element('article','coverage-card');card.append(element('span','',label),element('strong','',value),element('small','',note));grid.append(card);}
  host.append(grid);
  if(overview.reasons.length){const box=element('div','coverage-reasons'),list=element('ul');
    box.append(element('h3','',overview.blocked.length?'Cần xử lý để tiếp tục':'Điều gì còn thiếu?'));
    for(const reason of overview.reasons)list.append(element('li','',reason));box.append(list);
    if(overview.annualAvailable){const use=element('button','','Tạo phân tích mới với BCTC Năm');use.id='use-annual';availability(use,!draftChanged());
      use.onclick=()=>task(async()=>{await createAnalysis({...analysis.request,financial_basis:'annual'});message('Đã tạo lần phân tích BCTC Năm, giữ nguyên ngày chốt và kỳ giá. Bấm Phân tích & tạo báo cáo để chạy.');});box.append(use);}
    host.append(box);
  }
}
function renderDashboard() {
  $('dashboard-content').innerHTML = dashboardMarkup(analysis,{range:chartRange});
  for (const button of $('dashboard-content').querySelectorAll('[data-range]')) {
    button.onclick = () => { chartRange = button.dataset.range; renderDashboard(); $('dashboard-content').querySelector(`[data-range="${chartRange}"]`)?.focus({preventScroll:true}); };
  }
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function message(text, error = false) {
  $('notice').hidden = false;
  $('notice-text').textContent = text;
  $('notice').className = error ? 'error' : '';
  $('notice').setAttribute('role',error?'alert':'status');
  $('notice').setAttribute('aria-live',error?'assertive':'polite');
  $('connection-retry').hidden=!error;
  if(error)$('notice').scrollIntoView({block:'start'});
}
function availability(node, enabled, reason = '') {
  node.disabled = !enabled || busy;
  node.title = busy ? 'Đang xử lý, vui lòng chờ.' : enabled ? '' : reason;
}
async function api(route, body) {
  return requestJSON(route,body);
}
async function task(fn) {
  if (busy) return;
  busy = true;
  document.body.classList.add('busy');
  document.querySelector('.workspace').setAttribute('aria-busy', 'true');
  render();
  try { await fn(); }
  catch (e) { message(e.message, true); }
  finally {
    busy = false;
    document.body.classList.remove('busy');
    document.querySelector('.workspace').setAttribute('aria-busy', 'false');
    busyText='';
    render();
  }
}
function runUrl(action = '') {
  return '/api/runs/' + analysis.run_id + (action ? '/' + action : '');
}
function download(name) { window.location.href = runUrl('download/' + name); }
async function parseFile(file) {
  if (file.size > 20 * 1024 * 1024) throw Error('File vượt giới hạn 20 MB.');
  try { return JSON.parse((await file.text()).replace(/^\uFEFF/, '')); }
  catch { throw Error('Không đọc được JSON. Kiểm tra cú pháp và mã hóa UTF-8 của file.'); }
}
function render() {
  renderDashboard();
  renderOverview();
  $('run-title').textContent = analysis
    ? analysis.request.ticker + ' · ' + analysis.request.industry_name : 'Chưa tạo input';
  if(analysis)$('run-select').value=analysis.run_id;
  $('run-meta').textContent = analysis
    ? 'Ngày chốt ' + displayDate(analysis.request.as_of_date) + ' · ' + analysis.request.exchange + ' · ' + analysis.request.investment_horizon + ' (' + (analysis.request.investment_horizon_months || 'Chưa có') + ' tháng) · '+runLabel(analysis.request).split(' · ').slice(2,4).join(' · ')
    : 'Thiết lập mã cổ phiếu, ngành và kỳ phân tích để nhận dữ liệu của nhóm.';
  $('overall').textContent = analysis ? statusNames[analysis.overall_status] : 'Chờ input';
  $('overall').className = 'badge ' + (analysis?.overall_status || '');
  const ready = Object.values(analysis?.modules || {}).filter(m => m.status === 'ok').length;
  const processed = Object.values(analysis?.modules || {}).filter(m => !['pending'].includes(m.status)).length;
  $('progress').textContent = processed + ' / 4 module đã xử lý · ' + ready + ' hoàn chỉnh';
  $('next-action').textContent = !analysis
    ? 'Bước tiếp theo: tạo input ở bảng thiết lập.'
    : pdfAvailable ? 'Báo cáo đã sẵn sàng tải. Đọc phạm vi dữ liệu và phần còn thiếu trước khi sử dụng kết luận.'
    : processed===4 ? 'Đã xử lý đủ 4 phần. Xem phạm vi dữ liệu và cảnh báo; bạn có thể xuất báo cáo với các giới hạn được ghi rõ.'
    : 'Bấm Phân tích & tạo báo cáo để nhận dữ liệu, đánh giá chiến lược và xuất PDF.';
  $('busy-status').hidden=!busy;
  $('busy-status').textContent=busyText || 'Đang xử lý yêu cầu…';
  for (const id of ['request-download', 'analysis-download', 'preview']) {
    availability($(id), !!analysis, 'Tạo hoặc mở một lần phân tích trước.');
  }
  availability($('pipeline'), !!analysis && Object.keys(names).some(k => registry[k]),
    analysis ? 'Cài ít nhất một module trong phần Cài module của nhóm.' : 'Tạo input trước khi chạy module.');
  availability($('pdf-generate'), !!analysis && !!registry.pdf,
    registry.pdf ? 'Tạo input trước.' : 'Cần cài module PDF của người 6.');
  availability($('pdf-download'), !!analysis && pdfAvailable, 'Chưa có PDF được tạo cho lần phân tích này.');
  availability($('download-top'),!!analysis && pdfAvailable,'Chưa có PDF cho lần phân tích này.');
  availability($('hpg-preset'),true);
  availability($('package-upload'), true);
  availability($('connection-retry'),true);
  $('trusted').disabled = busy;
  $('package-file').disabled = busy;
  for(const field of $('request-form').querySelectorAll('input,select,button'))field.disabled=busy;
  $('run-select').disabled = busy;
  $('pdf-hint').textContent = pdfAvailable ? 'PDF thuộc đúng lần phân tích đang mở. Dữ liệu thay đổi sẽ làm PDF cũ hết hiệu lực.' : registry.pdf
    ? 'Có thể xuất PDF cả khi thiếu dữ liệu; báo cáo sẽ ghi rõ giới hạn và chưa có kết luận đủ điều kiện.'
    : 'Mở báo cáo rồi chọn In / Lưu PDF trong trình duyệt. Xuất PDF tự động cần module của người 6.';

  $('module-grid').replaceChildren();
  for (const key of Object.keys(names)) {
    const m = analysis?.modules[key];
    const card = element('article', 'module-card ' + key);
    card.setAttribute('aria-labelledby', 'module-title-' + key);
    const top = element('div', 'module-top');
    const icon = element('span', 'module-icon', icons[key]);
    icon.setAttribute('aria-hidden', 'true');
    top.append(icon, element('span', 'badge ' + (m?.status || ''), m ? statusNames[m.status] : 'Chờ input'));
    const title = element('h3', '', names[key]);
    title.id = 'module-title-' + key;
    const desc = element('p', 'hint description', descriptions[key]);
    const summary = element('div', 'module-summary', m
      ? (key === 'strategy' ? (m.data.rules?.length || 0) + ' quy tắc' : (m.data.metrics || []).filter(v => v.value !== null).length + '/' + (m.data.metrics?.length || 0) + ' chỉ số có số liệu') + ' · ' + m.sources.length + ' nguồn'
      : 'Tạo input để nhận output của nhóm.');
    const mode = element('span', 'module-mode', registry[key] ? 'MODULE ĐÃ CÀI' : 'NHẬN JSON TỪ THÀNH VIÊN');
    const toolbar = element('div', 'toolbar');
    const input = element('input');
    input.type = 'file'; input.accept = '.json'; input.hidden = true;
    input.disabled = !analysis || busy;
    input.addEventListener('change', () => {
      const file = input.files[0];
      if (file) task(async () => {
        const payload = await parseFile(file);
        const result = await api(runUrl('upload'), {module:key, payload});
        analysis = result.analysis;
        pdfAvailable = false;
        message('Đã nhận ' + names[key] + ' và kiểm tra hợp đồng dữ liệu.');
      });
    });
    const upload = element('button', 'upload-button', 'Tải lên JSON');
    upload.append(element('span', '', '↑'));
    upload.setAttribute('aria-label', 'Tải lên JSON ' + names[key]);
    availability(upload, !!analysis, 'Tạo input để nhận output.');
    upload.onclick = () => input.click();
    const run = element('button', '', 'Chạy module');
    run.dataset.runModule=key;
    run.setAttribute('aria-label', 'Chạy module ' + names[key]);
    availability(run, !!analysis && !!registry[key], registry[key] ? 'Tạo input trước.' : 'Chưa cài module ' + names[key] + '.');
    run.onclick = () => execute(key);
    const sample = element('button', '', 'Tải cấu trúc');
    sample.setAttribute('aria-label', 'Tải cấu trúc JSON ' + names[key]);
    availability(sample, !!analysis, 'Tạo input để tải cấu trúc đúng mã và kỳ.');
    sample.onclick = () => download(key + '.json');
    toolbar.append(upload, run, sample, input);
    const tools=element('details','module-tools');tools.append(element('summary','','Công cụ của nhóm: chạy riêng / nhận JSON'),mode,toolbar);
    card.append(top, title, desc, summary, tools);
    if (m?.warnings.length || m?.errors.length) card.append(element('p', 'hint module-warning', (m.errors[0] || m.warnings[0])));
    $('module-grid').append(card);
  }

  $('conclusion').replaceChildren();
  $('conclusion').className = analysis ? 'result' : 'empty';
  if (analysis) {
    $('conclusion').append(
      element('h3', '', labels[analysis.display_conclusion.label] || 'Chưa có kết luận'),
      element('p', '', analysis.display_conclusion.rationale)
    );
  } else $('conclusion').textContent = 'Báo cáo của bạn sẽ xuất hiện ở đây sau khi tạo input và nhận dữ liệu.';
  $('strategy-results').replaceChildren();
  const rules = analysis?.modules.strategy.data.rules || [];
  if (rules.length) {
    const details = element('details', 'strategy-details');
    details.append(element('summary', '', 'Chi tiết ' + rules.length + ' trụ cột chiến lược'));
    for (const rule of rules) {
      const item = element('div', 'strategy-rule');
      item.append(element('strong', '', (RULE_NAMES[rule.id] || rule.rule_id || rule.id) + ' · ' + (RULE_STATUS[rule.status] || rule.status || '')),
        element('p', 'hint', rule.explanation || ''));
      const values=element('details','rule-values');values.append(element('summary','','Xem dữ liệu và định danh quy tắc'),element('p','hint',rule.rule_id || rule.id),element('pre','',JSON.stringify(rule.values ?? {},null,2)));item.append(values);
      details.append(item);
    }
    $('strategy-results').append(details);
  }
  renderMetrics();
  const issues = analysis ? [...analysis.errors, ...analysis.warnings] : [];
  $('issue-count').textContent = analysis ? (issues.length ? issues.length + ' cần kiểm tra' : 'Không có cảnh báo') : 'Chưa có dữ liệu';
  $('issue-count').className = 'badge ' + (analysis?.errors.length ? 'error' : issues.length ? 'partial' : '');
  $('issues').replaceChildren();
  for (const text of issues.length ? issues : [analysis ? 'Không có lỗi/cảnh báo từ output hiện tại.' : 'Chưa có lần phân tích.']) {
    $('issues').append(element('li', '', text));
  }
  if (analysis?.errors.length) $('issues').closest('details').open = true;
  $('installed').textContent = Object.keys(registry).length
    ? 'Đã cài: ' + Object.keys(registry).map(k => names[k] || (k === 'pdf' ? 'PDF' : k)).join(', ')
    : 'Chưa cài module. Bạn vẫn có thể nhận JSON và xem / in báo cáo.';
  renderDraftState();
}
function renderMetrics() {
  $('metrics').replaceChildren();
  $('metric-filters').hidden=!analysis;
  $('metric-count').textContent='';
  if (analysis) {
    const allRows = Object.entries(analysis.modules).flatMap(([key,m]) => (m.data.metrics || []).map(metric=>({key,module:m,metric,presentation:metricPresentation(metric)})));
    const rows=allRows.filter(row=>matchesMetric(row.metric,row.key,{query:$('metric-search').value,section:$('metric-section').value,missingOnly:$('metric-missing').checked}));
    $('metric-count').textContent='Hiển thị '+rows.length+' / '+allRows.length+' chỉ số · '+allRows.filter(row=>row.metric.value===null).length+' chỉ số thiếu dữ liệu trong toàn bộ kết quả. Bộ lọc chỉ đổi bảng đang xem.';
    if (rows.length) {
      const table = element('table', 'metric-table');
      const head = element('thead'), header = element('tr'), body = element('tbody');
      for (const title of ['Chỉ số & kỳ dữ liệu', 'Giá trị', 'Đơn vị', 'Nguồn & phương pháp']) {
        const th = element('th', '', title); th.scope = 'col'; header.append(th);
      }
      head.append(header);
      for (const row of rows) {
        const tr = element('tr');
        const name=element('td','metric-name');name.append(element('strong','',row.presentation.label),element('small','',names[row.key]+' · '+row.presentation.period));
        const sourceCell=element('td'),details=element('details','metric-source');details.append(element('summary','','Xem nguồn ('+row.metric.source_refs.length+')'));
        details.append(element('p','',row.metric.value===null?(row.metric.missing_reason || 'Chưa đủ đầu vào để tính.'):'Giá trị gốc: '+String(row.metric.value)+' '+row.metric.unit));
        details.append(element('code','',row.metric.metric_id));
        if(row.metric.formula_id)details.append(element('p','', 'Công thức: '+row.metric.formula_id));
        const list=element('ul');
        for(const ref of row.metric.source_refs){const s=row.module.sources.find(source=>source.source_id===ref);if(!s)continue;
          const li=element('li'),link=element('a','',s.title);link.href=s.url;link.target='_blank';link.rel='noopener noreferrer';
          const eligible=s.publication_date_verified && s.published_at && s.published_at.slice(0,10)<=analysis.request.as_of_date;
          li.append(link,element('p','', 'Công bố: '+displayDate(s.published_at)+' · '+(eligible?'Đủ điều kiện ngày chốt':'Chưa đủ điều kiện ngày chốt')));list.append(li);}
        details.append(list);sourceCell.append(details);
        tr.append(name,element('td','',row.presentation.value),element('td','',row.presentation.unit),sourceCell);
        body.append(tr);
      }
      table.append(head, body); $('metrics').append(table);
    } else $('metrics').append(element('p','hint',allRows.length?'Không có chỉ số khớp bộ lọc. Xóa bộ lọc để xem lại toàn bộ.':'Chưa có chỉ số. Chạy phân tích hoặc nhận dữ liệu của nhóm.'));
  }
}
async function loadRuns() {
  const result = await api('/api/runs');
  $('run-select').replaceChildren(new Option('Chọn lần phân tích', ''));
  for (const request of result.runs) {
    $('run-select').add(new Option(runLabel(request), request.run_id));
  }
  if (analysis) $('run-select').value = analysis.run_id;
}
async function execute(module) {
  await task(async () => {
    busyText=module?'Đang xử lý '+names[module]+'…':'Đang lấy Vĩ mô, Ngành, Doanh nghiệp song song; sau đó đánh giá chiến lược…';render();
    const result = await api(runUrl(module ? 'execute' : 'pipeline'), {module, confirm_execution:true});
    analysis = result.analysis;
    // Re-read PDF state because a failed execution can retain the previous artifact.
    const current = await api(runUrl());
    pdfAvailable = current.pdf_available;
    $('execution').hidden = false;
    $('execution').textContent = result.execution.map(e => names[e.module] + ': ' + ({saved:'Đã xử lý',skipped:'Chưa cài',error:'Có lỗi'}[e.status] || e.status) + (e.message ? ' — ' + e.message : '')).join('\n');
    const failed = result.execution.some(e => e.status === 'error')
      || Object.values(analysis.modules).some(m => m.status === 'error');
    if (!module && !failed && registry.pdf) {
      busyText='Đã nhận dữ liệu và đánh giá chiến lược. Đang tạo báo cáo PDF…';render();
      message('Đã ghép dữ liệu và chiến lược. Đang tạo PDF…');
      await api(runUrl('pdf'), {confirm_execution:true});
      pdfAvailable = true;
    }
    if(failed)$('execution').closest('details').open=true;
    message(failed ? 'Có phần chạy lỗi: xem nhật ký và thử chạy lại phần đó.'
      : !module && pdfAvailable ? 'Đã tạo báo cáo. PDF sẵn sàng; xem phần còn thiếu và phạm vi dữ liệu trước khi sử dụng.' : 'Đã xử lý '+(names[module] || 'dữ liệu')+'.', failed);
  });
}
$('request-form').onsubmit = e => {
  e.preventDefault();
  const request = formRequest();
  task(async () => {
    await createAnalysis(request);
    message('Đã lưu cấu hình. Bấm Phân tích & tạo báo cáo để tiếp tục.');
  });
};
$('run-select').onchange = e => {
  const id = e.target.value;
  if(analysis)$('run-select').value=analysis.run_id;
  if (id) task(async () => {
    await openRun(id);
  });
};
$('package-upload').onclick = () => $('package-file').click();
$('package-file').onchange = e => {
  const file = e.target.files[0];
  if (!file) return;
  task(async () => {
    if (!$('trusted').checked) throw Error('Cần xác nhận tin cậy mã nguồn trước khi cài.');
    const pkg = await parseFile(file);
    const result = await api('/api/modules/install', {trusted:true, package:pkg});
    registry = result.registry; $('trusted').checked = false;
    message('Đã cài ' + pkg.module + '. Chỉ chạy khi bạn bấm Chạy module.');
  }).finally(() => e.target.value = '');
};
$('notice-close').onclick = () => $('notice').hidden = true;
$('start').onclick = e => {
  e.preventDefault();
  $('setup').scrollIntoView({block:'start'});
  $('request-form').elements.namedItem('ticker').focus({preventScroll:true});
};
$('pipeline').onclick = () => execute();
$('download-top').onclick = () => download('report.pdf');
$('request-form').addEventListener('input',()=>{if(!busy)saveDraft();renderDraftState();});
$('request-form').addEventListener('change',()=>{if(!busy)saveDraft();renderDraftState();});
$('draft-discard').onclick=()=>{syncForm();draftNote='';try{localStorage.removeItem(draftKey());}catch{}renderDraftState();};
for(const id of ['metric-search','metric-section','metric-missing'])$(id).addEventListener(id==='metric-search'?'input':'change',renderMetrics);
$('metric-reset').onclick=()=>{$('metric-search').value='';$('metric-section').value='all';$('metric-missing').checked=false;renderMetrics();};
$('hpg-preset').onclick = () => {
  const preset={ticker:'HPG',exchange:'HOSE',industry_name:'',as_of_date:'2026-10-09',period_start:'2025-01-01',period_end:'2026-10-08',investment_horizon:'Trung hạn',investment_horizon_months:12,financial_basis:'annual',statement_scope:'consolidated'};
  for(const [key,value] of Object.entries(preset))$('request-form').elements.namedItem(key).value=value;
  saveDraft();renderDraftState();message('Đã điền cấu hình snapshot HPG. Bạn có thể chỉnh lại trước khi Tạo lần phân tích.');
};
$('request-download').onclick = () => download('request.json');
$('analysis-download').onclick = () => download('analysis.json');
$('preview').onclick = () => window.open(runUrl('report'), '_blank', 'noopener');
$('pdf-download').onclick = () => download('report.pdf');
$('pdf-generate').onclick = () => task(async () => {
  await api(runUrl('pdf'), {confirm_execution:true});
  pdfAvailable = true;
  message('Đã tạo PDF và kiểm tra manifest. Bạn có thể tải xuống.');
});
function renderTheme() {
  const light = document.documentElement.dataset.theme === 'light';
  $('theme-toggle').textContent = light ? '☾ Tối' : '☀ Sáng';
  $('theme-toggle').setAttribute('aria-label', light ? 'Chuyển sang giao diện tối' : 'Chuyển sang giao diện sáng');
  $('theme-toggle').setAttribute('aria-pressed', String(light));
  document.querySelector('meta[name="theme-color"]').content = light ? '#f4f6f0' : '#08090b';
}
$('theme-toggle').onclick = () => {
  document.documentElement.dataset.theme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
  try { localStorage.setItem('hub-theme', document.documentElement.dataset.theme); } catch {}
  renderTheme();
};
async function reconnect() {
 await task(async () => {
  const result = await api('/api/modules');
  registry = result.registry;
  let previous;try{previous=localStorage.getItem('mmb-last-run');}catch{}
  if(previous && /^[a-f0-9-]{36}$/.test(previous)){
    try{await openRun(previous);}catch(e){if(e.status!==404)throw e;if(analysis?.run_id===previous){analysis=null;pdfAvailable=false;}try{localStorage.removeItem('mmb-last-run');}catch{}}
  }
  if(!analysis)restoreDraft();
  await loadRuns();
  $('notice').hidden=true;
 });
}
$('connection-retry').onclick=()=>reconnect();
renderTheme();
render();
reconnect();
