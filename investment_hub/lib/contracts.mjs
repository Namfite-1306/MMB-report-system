import {resolveIndustry} from './industries.mjs';
export const VERSION = '1.0';
export const DATA_MODULES = ['macro', 'industry', 'company'];
export const MODULES = [...DATA_MODULES, 'strategy'];
export const LABELS = ['attractive', 'watchlist', 'unattractive', 'insufficient_data'];
export function assert(ok, message) { if (!ok) throw new Error(message); }
const obj = v => v && typeof v === 'object' && !Array.isArray(v);
const str = v => typeof v === 'string' && v.trim().length > 0;
export function validDate(v) {
  return typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v)
    && Number.isFinite(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v;
}
export function now() { return new Date(Date.now() + 7 * 3600_000).toISOString().replace('Z', '+07:00'); }
function timestamp(v) { return str(v) && /^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(v) && Number.isFinite(Date.parse(v)); }
export function validateRequest(input, runId) {
  assert(obj(input), 'Input phải là object.');
  const ticker = String(input.ticker || '').trim().toUpperCase();
  assert(/^[A-Z0-9]{2,12}$/.test(ticker), 'Mã cổ phiếu phải gồm 2–12 chữ/số.');
  assert(['HOSE', 'HNX', 'UPCOM'].includes(input.exchange), 'Sàn phải là HOSE/HNX/UPCOM.');
  const industry = resolveIndustry(ticker);
  assert(str(input.investment_horizon), 'Thiếu investment_horizon.');
  for (const field of ['as_of_date', 'period_start', 'period_end']) assert(validDate(input[field]), `${field} phải là ngày YYYY-MM-DD hợp lệ.`);
  assert(input.period_start <= input.period_end && input.period_end <= input.as_of_date, 'Cần ngày bắt đầu ≤ ngày kết thúc ≤ ngày chốt.');
  const options = {};
  if (input.investment_horizon_months !== undefined && input.investment_horizon_months !== '') {
    const months = Number(input.investment_horizon_months);
    assert(Number.isInteger(months) && months > 0 && months <= 600, 'Số tháng đầu tư phải là số nguyên từ 1 đến 600.');
    options.investment_horizon_months = months;
  }
  for (const [key, allowed] of Object.entries({financial_basis:['annual','ytd','quarterly','ttm'],statement_scope:['consolidated','separate']})) {
    if (input[key] !== undefined) { assert(allowed.includes(input[key]), `${key} không hợp lệ.`); options[key] = input[key]; }
  }
  return {schema_version: VERSION, run_id: runId, ticker, exchange: input.exchange, ...options,
    industry_code: str(input.industry_code) ? input.industry_code.trim() : industry.code,
    industry_name: str(input.industry_name) ? input.industry_name.trim() : industry.name,
    as_of_date: input.as_of_date, period_start: input.period_start, period_end: input.period_end,
    investment_horizon: input.investment_horizon.trim(), language: 'vi', currency: 'VND'};
}
export function pending(request, module) {
  const data = {metrics: [], findings: [], risks: []};
  if (module === 'industry') Object.assign(data, {industry_code: request.industry_code, peers: []});
  if (module === 'company') Object.assign(data, {price_series: [], financials: []});
  if (module === 'strategy') Object.assign(data, {theory_sources: [], rules: [], evidence_refs: [],
    conclusion: {label: 'insufficient_data', rationale: 'Chưa nhận module chiến lược.', evidence_refs: [], horizon: request.investment_horizon}});
  return {schema_version: VERSION, run_id: request.run_id, module, ticker: request.ticker,
    as_of_date: request.as_of_date, generated_at: now(), status: 'pending', data, sources: [], warnings: ['Chưa có dữ liệu thật.'], errors: []};
}
export function validateEnvelope(value, request, module) {
  assert(obj(value) && MODULES.includes(module), 'Module không hợp lệ.');
  for (const [key, expected] of Object.entries({schema_version: VERSION, run_id: request.run_id, module, ticker: request.ticker, as_of_date: request.as_of_date}))
    assert(value[key] === expected, `${module}.${key}: phải bằng ${expected}. Không tự sửa định danh file.`);
  assert(timestamp(value.generated_at), `${module}.generated_at phải là ISO8601 có múi giờ.`);
  assert(['pending','ok','partial','error'].includes(value.status), `${module}.status không hợp lệ.`);
  assert(obj(value.data), `${module}.data phải là object.`);
  for (const key of ['sources','warnings','errors']) assert(Array.isArray(value[key]), `${module}.${key} phải là mảng.`);
  assert(value.warnings.every(v => typeof v === 'string') && value.errors.every(v => typeof v === 'string'), 'warnings/errors chỉ nhận chuỗi.');
  assert(value.status !== 'ok' || value.errors.length === 0, 'Không dùng status=ok khi còn errors.');
  const prefix = id => str(id) && id.startsWith(`${module}:`);
  const sourceIds = new Set();
  for (const source of value.sources) {
    assert(obj(source) && prefix(source.source_id) && !sourceIds.has(source.source_id), `${module}: source_id phải duy nhất và bắt đầu bằng '${module}:'.`);
    sourceIds.add(source.source_id);
    assert(str(source.title) && str(source.url), 'Nguồn cần title và url.');
    try { assert(['https:', 'http:'].includes(new URL(source.url).protocol), 'Nguồn phải dùng HTTP(S).'); } catch { throw new Error('URL nguồn không hợp lệ.'); }
    assert(timestamp(source.retrieved_at), 'retrieved_at cần ISO8601 có múi giờ.');
    assert(source.published_at === null || validDate(source.published_at) || timestamp(source.published_at), 'published_at cần ngày/timestamp hợp lệ hoặc null.');
    assert(typeof source.publication_date_verified === 'boolean', 'Thiếu publication_date_verified.');
    assert(source.locator === null || typeof source.locator === 'string', 'locator phải là chuỗi hoặc null.');
  }
  const refs = (list, local = true) => {
    assert(Array.isArray(list) && list.every(str), 'evidence_refs/source_refs phải là mảng ID.');
    if (local) for (const id of list) assert(sourceIds.has(id), `Nguồn không tồn tại: ${id}.`);
  };
  const records = key => { assert(Array.isArray(value.data[key]), `${module}.data.${key} phải là mảng.`); return value.data[key]; };
  const number = n => n === null || (typeof n === 'number' && Number.isFinite(n));
  const metricIds = new Set();
  if (module !== 'strategy') {
    for (const metric of records('metrics')) {
      assert(obj(metric) && prefix(metric.metric_id) && !metricIds.has(metric.metric_id), 'metric_id trùng hoặc thiếu prefix module.');
      metricIds.add(metric.metric_id);
      assert(number(metric.value), 'value phải là số hữu hạn hoặc null.');
      assert(str(metric.unit) && str(metric.frequency), 'Chỉ số thiếu unit/frequency.');
      assert(validDate(metric.period_start) && validDate(metric.period_end) && metric.period_start <= metric.period_end && metric.period_end <= request.as_of_date, 'Kỳ chỉ số không hợp lệ hoặc vượt ngày chốt.');
      assert(metric.formula_id === null || str(metric.formula_id), 'formula_id phải là chuỗi hoặc null.');
      refs(metric.source_refs); assert(metric.value === null || metric.source_refs.length > 0, 'Chỉ số có giá trị phải có nguồn.');
    }
    for (const key of ['findings','risks']) for (const item of records(key)) {
      assert(obj(item) && str(item.text), `${key} phải có text.`); refs(item.evidence_refs, false);
      for (const id of item.evidence_refs) assert(sourceIds.has(id) || metricIds.has(id), `Bằng chứng không tồn tại trong module: ${id}.`);
    }
  }
  if (module === 'industry') { assert(value.data.industry_code === request.industry_code, 'Mã ngành không khớp input.'); records('peers'); }
  if (module === 'company') {
    for (const row of records('price_series')) {
      assert(validDate(row.date) && row.date <= request.as_of_date, 'Ngày giá không hợp lệ.');
      assert(number(row.close) && number(row.volume) && str(row.adjustment_basis), 'Giá/khối lượng phải là số hoặc null, cần adjustment_basis.'); refs(row.source_refs);
      assert((row.close === null && row.volume === null) || row.source_refs.length > 0, 'Giá/khối lượng có giá trị phải có nguồn.');
    }
    for (const row of records('financials')) {
      assert(str(row.item_id) && number(row.value) && str(row.unit) && str(row.statement_scope), 'BCTC thiếu item_id/value/unit/statement_scope.');
      assert(validDate(row.period_start) && validDate(row.period_end) && row.period_start <= row.period_end && row.period_end <= request.as_of_date, 'Kỳ BCTC không hợp lệ.'); refs(row.source_refs);
      assert(row.value === null || row.source_refs.length > 0, 'BCTC có số phải có nguồn.');
    }
  }
  if (module === 'strategy') {
    records('theory_sources'); records('rules'); records('risks'); refs(value.data.evidence_refs, false);
    const conclusion = value.data.conclusion;
    assert(obj(conclusion) && LABELS.includes(conclusion.label) && str(conclusion.rationale), 'Kết luận chiến lược không hợp lệ.');
    assert(conclusion.horizon === request.investment_horizon, 'Thời hạn chiến lược không khớp input.'); refs(conclusion.evidence_refs, false);
    if (value.status === 'ok' && conclusion.label !== 'insufficient_data') {
      assert(value.data.theory_sources.length > 0 && value.data.rules.length > 0 && conclusion.evidence_refs.length > 0, 'Kết luận cần lý thuyết, quy tắc và bằng chứng.');
    }
  }
  return value;
}
export function assemble(request, modules) {
  const warnings = [], errors = [], available = new Set(), eligible = new Set();
  for (const module of MODULES) {
    const v = validateEnvelope(modules[module], request, module);
    warnings.push(...v.warnings.map(t => `${module}: ${t}`)); errors.push(...v.errors.map(t => `${module}: ${t}`));
    if (v.status === 'ok' && module !== 'strategy' && !(v.data.metrics.length || (v.data.price_series?.length) || (v.data.financials?.length))) warnings.push(`${module}: status=ok nhưng chưa có dữ liệu định lượng.`);
    for (const src of v.sources) {
      available.add(src.source_id);
      if (src.publication_date_verified && src.published_at && src.published_at.slice(0,10) <= request.as_of_date) eligible.add(src.source_id);
      else warnings.push(`${module}: nguồn ${src.source_id} chưa đủ điều kiện tại ngày chốt.`);
    }
    for (const metric of v.data.metrics || []) {
      available.add(metric.metric_id);
      if (metric.value !== null && metric.source_refs.length && metric.source_refs.every(id => eligible.has(id))) eligible.add(metric.metric_id);
      else warnings.push(`${module}: chỉ số ${metric.metric_id} thiếu số hoặc nguồn đủ điều kiện.`);
    }
  }
  const strategy = modules.strategy;
  const missing = DATA_MODULES.filter(k => modules[k].status !== 'ok');
  const evidence = [...strategy.data.evidence_refs, ...strategy.data.conclusion.evidence_refs];
  for (const ref of evidence) if (!available.has(ref)) errors.push(`strategy: bằng chứng không tồn tại: ${ref}.`);
  const ineligible = evidence.filter(ref => !eligible.has(ref));
  const conclusionUsable = strategy.status === 'ok' && !missing.length && !ineligible.length && !errors.length
    && !warnings.length && strategy.data.conclusion.label !== 'insufficient_data';
  if (missing.length) warnings.push(`Chờ dữ liệu hoàn chỉnh: ${missing.join(', ')}.`);
  if (ineligible.length) warnings.push('Kết luận chứa bằng chứng chưa đủ điều kiện tại ngày chốt.');
  return {schema_version: VERSION, run_id: request.run_id, request, generated_at: now(), modules,
    overall_status: errors.length || MODULES.some(k => modules[k].status === 'error') ? 'error' :
      MODULES.every(k => modules[k].status === 'pending') ? 'pending' :
        MODULES.every(k => modules[k].status === 'ok') && !warnings.length ? 'ok' : 'partial',
    conclusion_usable: conclusionUsable,
    display_conclusion: conclusionUsable ? strategy.data.conclusion : {label: 'insufficient_data', rationale: 'Chưa đủ dữ liệu/bằng chứng được kiểm chứng để sử dụng kết luận.', evidence_refs: [], horizon: request.investment_horizon},
    warnings: [...new Set(warnings)], errors: [...new Set(errors)]};
}
