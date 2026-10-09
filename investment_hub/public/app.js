import {dashboardMarkup} from './dashboard.js';
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
function renderDashboard() {
  $('dashboard-content').innerHTML = dashboardMarkup(analysis,{range:chartRange});
  for (const button of $('dashboard-content').querySelectorAll('[data-range]')) {
    button.onclick = () => { chartRange = button.dataset.range; renderDashboard(); };
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
}
function availability(node, enabled, reason = '') {
  node.disabled = !enabled || busy;
  node.title = busy ? 'Đang xử lý, vui lòng chờ.' : enabled ? '' : reason;
}
async function api(route, body) {
  const response = await fetch(route, body === undefined ? {} : {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)
  });
  const result = await response.json();
  if (!response.ok) throw Error(result.error || 'Yêu cầu thất bại.');
  return result;
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
  $('run-title').textContent = analysis
    ? analysis.request.ticker + ' · ' + analysis.request.industry_name : 'Chưa tạo input';
  $('run-meta').textContent = analysis
    ? 'Ngày chốt ' + analysis.request.as_of_date + ' · ' + analysis.request.investment_horizon + ' · Run ' + analysis.run_id
    : 'Thiết lập mã cổ phiếu, ngành và kỳ phân tích để nhận dữ liệu của nhóm.';
  $('overall').textContent = analysis ? statusNames[analysis.overall_status] : 'Chờ input';
  $('overall').className = 'badge ' + (analysis?.overall_status || '');
  const ready = Object.values(analysis?.modules || {}).filter(m => m.status === 'ok').length;
  const processed = Object.values(analysis?.modules || {}).filter(m => !['pending'].includes(m.status)).length;
  $('progress').textContent = processed + ' / 4 module đã xử lý · ' + ready + ' hoàn chỉnh';
  $('next-action').textContent = !analysis
    ? 'Bước tiếp theo: tạo input ở bảng thiết lập.'
    : ready === 4 ? 'Đã nhận đủ 4 đầu ra. Kiểm tra cảnh báo và kết quả trước khi xuất báo cáo.'
    : 'Bước tiếp theo: bấm Chạy workflow & tạo PDF, hoặc tải lên JSON mới từ nhóm. Trạng thái Một phần vẫn có thể xuất báo cáo với cảnh báo.';
  for (const id of ['request-download', 'analysis-download', 'preview']) {
    availability($(id), !!analysis, 'Tạo hoặc mở một lần phân tích trước.');
  }
  availability($('pipeline'), !!analysis && Object.keys(names).some(k => registry[k]),
    analysis ? 'Cài ít nhất một module trong phần Cài module của nhóm.' : 'Tạo input trước khi chạy module.');
  availability($('pdf-generate'), !!analysis && !!registry.pdf,
    registry.pdf ? 'Tạo input trước.' : 'Cần cài module PDF của người 6.');
  availability($('pdf-download'), !!analysis && pdfAvailable, 'Chưa có PDF được tạo cho lần phân tích này.');
  availability($('package-upload'), true);
  $('trusted').disabled = busy;
  $('package-file').disabled = busy;
  $('request-form').querySelector('button').disabled = busy;
  $('run-select').disabled = busy;
  $('pdf-hint').textContent = registry.pdf
    ? 'Module PDF đã cài. Bấm Tạo PDF bằng module, sau đó tải file. Bạn cũng có thể xem / in báo cáo.'
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
    run.setAttribute('aria-label', 'Chạy module ' + names[key]);
    availability(run, !!analysis && !!registry[key], registry[key] ? 'Tạo input trước.' : 'Chưa cài module ' + names[key] + '.');
    run.onclick = () => execute(key);
    const sample = element('button', '', 'Tải cấu trúc');
    sample.setAttribute('aria-label', 'Tải cấu trúc JSON ' + names[key]);
    availability(sample, !!analysis, 'Tạo input để tải cấu trúc đúng mã và kỳ.');
    sample.onclick = () => download(key + '.json');
    toolbar.append(upload, run, sample, input);
    card.append(top, title, desc, summary, mode, toolbar);
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
      item.append(element('strong', '', (rule.rule_id || rule.id) + ' · ' + (rule.status || '')),
        element('p', 'hint', rule.explanation || ''),
        element('pre', '', JSON.stringify(rule.values ?? {}, null, 2)));
      details.append(item);
    }
    $('strategy-results').append(details);
  }
  $('metrics').replaceChildren();
  if (analysis) {
    const rows = Object.values(analysis.modules).flatMap(m => (m.data.metrics || []).map(v =>
      [v.metric_id, v.value === null ? 'Chưa có' : String(v.value), v.unit]));
    if (rows.length) {
      const table = element('table', 'metric-table');
      const head = element('thead'), header = element('tr'), body = element('tbody');
      for (const title of ['Chỉ số', 'Giá trị', 'Đơn vị']) {
        const th = element('th', '', title); th.scope = 'col'; header.append(th);
      }
      head.append(header);
      for (const row of rows) {
        const tr = element('tr');
        for (const value of row) tr.append(element('td', '', value));
        body.append(tr);
      }
      table.append(head, body); $('metrics').append(table);
    }
  }
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
}
async function loadRuns() {
  const result = await api('/api/runs');
  $('run-select').replaceChildren(new Option('Chọn lần phân tích', ''));
  for (const request of result.runs) {
    $('run-select').add(new Option(request.ticker + ' · ' + request.as_of_date + ' · ' + request.run_id.slice(0,8), request.run_id));
  }
  if (analysis) $('run-select').value = analysis.run_id;
}
async function execute(module) {
  await task(async () => {
    const result = await api(runUrl(module ? 'execute' : 'pipeline'), {module, confirm_execution:true});
    analysis = result.analysis;
    // Re-read PDF state because a failed execution can retain the previous artifact.
    const current = await api(runUrl());
    pdfAvailable = current.pdf_available;
    $('execution').hidden = false;
    $('execution').textContent = result.execution.map(e => e.module + ': ' + e.status + (e.message ? ' — ' + e.message : '')).join('\n');
    $('execution').closest('details').open = true;
    const failed = result.execution.some(e => e.status === 'error')
      || Object.values(analysis.modules).some(m => m.status === 'error');
    if (!module && !failed && registry.pdf) {
      message('Đã ghép dữ liệu và chiến lược. Đang tạo PDF…');
      await api(runUrl('pdf'), {confirm_execution:true});
      pdfAvailable = true;
    }
    message(failed ? 'Có module chạy lỗi; xem nhật ký. Output hợp lệ trước đó được giữ lại.'
      : !module && pdfAvailable ? 'Workflow đã hoàn tất. PDF sẵn sàng tải; kiểm tra các cảnh báo chất lượng dữ liệu.' : 'Đã xử lý module.', failed);
  });
}
$('request-form').onsubmit = e => {
  e.preventDefault();
  task(async () => {
    const request = Object.fromEntries(new FormData(e.target));
    const result = await api('/api/runs', request);
    analysis = result.analysis; pdfAvailable = false; $('execution').hidden = true;
    chartRange = 'all';
    $('request-form').elements.namedItem('industry_name').value = analysis.request.industry_name;
    await loadRuns();
    message('Đã tạo input chung. Bấm Chạy workflow & tạo PDF để xử lý các phần đã tích hợp.');
  });
};
$('run-select').onchange = e => {
  const id = e.target.value;
  if (id) task(async () => {
    const result = await api('/api/runs/' + id);
    analysis = result.analysis; pdfAvailable = result.pdf_available; $('execution').hidden = true;
    chartRange = 'all';
    for (const [key, value] of Object.entries(analysis.request)) {
      const field = $('request-form').elements.namedItem(key);
      if (field) field.value = value;
    }
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
renderTheme();
render();
task(async () => {
  const result = await api('/api/modules');
  registry = result.registry;
  await loadRuns();
});
