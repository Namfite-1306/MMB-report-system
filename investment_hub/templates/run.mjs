// Skeleton bàn giao. Thay MODULE và phần xử lý bằng logic/dữ liệu thật của bạn.
// Không có số liệu, công thức đầu tư hoặc kết luận được tạo sẵn.
const MODULE = 'strategy';
let text = ''; for await (const chunk of process.stdin) text += chunk;
const input = JSON.parse(text), request = input.request;
const data = {metrics: [], findings: [], risks: []};
if (MODULE === 'industry') Object.assign(data, {industry_code: request.industry_code, peers: []});
if (MODULE === 'company') Object.assign(data, {price_series: [], financials: []});
if (MODULE === 'strategy') Object.assign(data, {theory_sources: [], rules: [], evidence_refs: [], conclusion: {
  label: 'insufficient_data', rationale: 'Module chưa được triển khai.', evidence_refs: [], horizon: request.investment_horizon}});
const output = {schema_version: request.schema_version, run_id: request.run_id, module: MODULE,
  ticker: request.ticker, as_of_date: request.as_of_date, generated_at: new Date().toISOString(),
  status: 'pending', data, sources: [], warnings: ['Skeleton chưa có logic hoặc dữ liệu thật.'], errors: []};
console.log(JSON.stringify(output));
