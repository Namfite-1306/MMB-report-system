const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
import {dashboardMarkup} from '../public/dashboard.js';
const names = {macro:'Vĩ mô',industry:'Ngành',company:'Doanh nghiệp',strategy:'Chiến lược'};
const labels = {attractive:'Có cơ hội',watchlist:'Theo dõi',unattractive:'Chưa hấp dẫn',insufficient_data:'Chưa đủ dữ liệu'};
export function renderReport(analysis) {
  const r = analysis.request;
  const sections = Object.entries(analysis.modules).map(([key,m]) => {
    const metrics = (m.data.metrics || []).map(v => `<tr><td>${escape(v.metric_id)}</td><td>${v.value === null ? 'Chưa có' : escape(v.value)}</td><td>${escape(v.unit)}</td><td>${escape(v.period_start)} — ${escape(v.period_end)}</td></tr>`).join('');
    const sources = m.sources.map(v => `<li>${escape(v.source_id)}: <a href="${escape(v.url)}">${escape(v.title)}</a> — công bố: ${escape(v.published_at || 'Chưa xác minh')} ${escape(v.locator || '')}</li>`).join('');
    const strategy = key === 'strategy' ? `<h3>Cơ sở lý thuyết</h3><ul>${(m.data.theory_sources || []).map(t=>`<li>${escape(t.title)} — ${escape(t.pages || 'Chưa xác minh trang')} — ${escape(t.url)}</li>`).join('')}</ul><h3>Quy tắc và kết quả</h3>${(m.data.rules || []).map(rule=>`<h4>${escape(rule.rule_id)} · ${escape(rule.status)}</h4><p>${escape(rule.formula)}</p><p>${escape(rule.explanation)}</p><pre>${escape(JSON.stringify(rule.values ?? {},null,2))}</pre>`).join('')}` : '';
    return `<section><h2>${names[key]}</h2><p>Trạng thái: ${escape(m.status)}</p>${metrics ? `<table><thead><tr><th>Chỉ số</th><th>Giá trị</th><th>Đơn vị</th><th>Kỳ</th></tr></thead><tbody>${metrics}</tbody></table>` : key==='strategy' ? '' : '<p>Chưa có bảng chỉ số.</p>'}${strategy}
      ${(m.data.findings || []).map(v => `<p>${escape(v.text)}</p>`).join('')}
      ${(m.data.risks || []).map(v => `<p><strong>Rủi ro:</strong> ${escape(v.text || v)}</p>`).join('')}
      <h3>Nguồn</h3><ul>${sources || '<li>Chưa có nguồn.</li>'}</ul></section>`;
  }).join('');
  return `<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MMB Analysis · ${escape(r.ticker)}</title><link rel="stylesheet" href="/dashboard.css">
  <style>body{font:15px/1.6 Arial,sans-serif;color:#183047;max-width:960px;margin:35px auto;padding:20px}h1,h2{color:#183f63}section{margin:30px 0}table{width:100%;border-collapse:collapse;font-size:13px}td,th{text-align:left;border-bottom:1px solid #d8e1e9;padding:10px;overflow-wrap:anywhere}a{color:#225b85;overflow-wrap:anywhere}ul{padding-left:22px}.notice{background:#fff3d8;padding:18px}button{padding:12px 20px;border:0;background:#183f63;color:white;border-radius:8px;cursor:pointer}@media print{button{display:none}body{margin:0;max-width:none;padding:0}h2,h3{break-after:avoid}tr{break-inside:avoid}a{color:inherit}thead{display:table-header-group}}@page{size:A4;margin:18mm}</style>
  <button onclick="window.print()">In / Lưu PDF</button><p>MMB ANALYSIS</p><h1>Phân tích cơ hội đầu tư ${escape(r.ticker)}</h1><p>${escape(r.industry_name)} · ${escape(r.exchange)} · Ngày chốt: ${escape(r.as_of_date)}</p><p>Kỳ phân tích: ${escape(r.period_start)} — ${escape(r.period_end)}. Thời hạn: ${escape(r.investment_horizon)}.</p>
  <div class="notice"><strong>${labels[analysis.display_conclusion.label]}</strong><p>${escape(analysis.display_conclusion.rationale)}</p><p>Trạng thái tổng: ${escape(analysis.overall_status)}. Run: ${escape(r.run_id)}</p></div>
  <section><h2>Dashboard phân tích</h2>${dashboardMarkup(analysis,{interactive:false})}</section>${sections}<section><h2>Cảnh báo và giới hạn</h2><ul>${[...analysis.warnings,...analysis.errors].map(v=>`<li>${escape(v)}</li>`).join('') || '<li>Không có cảnh báo từ các module đã bàn giao.</li>'}</ul></section></html>`;
}
