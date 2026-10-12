import {buildDashboardData} from './dashboard.js';

export const MODULE_NAMES={macro:'Vĩ mô',industry:'Ngành',company:'Doanh nghiệp',strategy:'Chiến lược'};
export const BASIS_NAMES={annual:'Năm',quarterly:'Quý',ytd:'Lũy kế (YTD)',ttm:'12 tháng (TTM)'};
export const RULE_NAMES={macro:'Bối cảnh vĩ mô',industry:'Triển vọng ngành',fundamental:'Sức khỏe tài chính',value:'Đầu tư giá trị',relative_valuation:'Định giá so sánh',momentum:'Xu hướng giá',risk:'Rủi ro danh mục',capm:'Lợi suất yêu cầu (CAPM)',news:'Tin tức và sự kiện'};
export const RULE_STATUS={evaluated:'Đã đánh giá',insufficient_data:'Thiếu dữ liệu',not_applicable:'Không áp dụng',error:'Có lỗi',pending:'Đang chờ'};
export function runLabel(request) {
  return [request.ticker,displayDate(request.as_of_date),BASIS_NAMES[request.financial_basis] || 'Năm',request.statement_scope==='separate'?'Riêng lẻ':'Hợp nhất',request.run_id.slice(0,8)].join(' · ');
}
const searchable=value=>String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[đĐ]/g,'d').toLowerCase();
export function matchesMetric(metric,module,{query='',section='all',missingOnly=false}={}) {
  if(section!=='all' && module!==section)return false;
  if(missingOnly && metric.value!==null)return false;
  const text=searchable([metricPresentation(metric).label,metric.metric_id,metric.period_start,metric.period_end].join(' '));
  return searchable(query).trim().split(/\s+/).every(term=>text.includes(term));
}
const METRIC_NAMES={vn_real_gdp_growth_annual_yoy_2024:'Tăng trưởng GDP thực 2024',vn_cpi_average_growth_annual_yoy_2024:'Lạm phát bình quân 2024',vn_sbv_refinancing_rate_effective_2023_06_19:'Lãi suất tái cấp vốn',vn_sbv_central_usd_vnd_2025_01_06:'Tỷ giá trung tâm USD/VND',ind_pe_median:'P/E trung vị nhóm ngành',ind_pb_median:'P/B trung vị nhóm ngành',ind_roe_avg:'ROE bình quân nhóm ngành',ind_net_margin_avg:'Biên lợi nhuận ròng nhóm ngành',ind_crude_steel_consumption_growth:'Tăng trưởng tiêu thụ thép thô',ind_iip_metal_growth:'Tăng trưởng sản xuất kim loại'};
const num=(value,digits=2)=>new Intl.NumberFormat('vi-VN',{maximumFractionDigits:digits}).format(value);
export function displayDate(value) {
  const date=String(value || '').slice(0,10);
  return /^\d{4}-\d{2}-\d{2}$/.test(date)?date.slice(8)+'/'+date.slice(5,7)+'/'+date.slice(0,4):'Chưa xác định';
}
export function metricPresentation(metric) {
  const id=metric.metric_id.split(':').at(-1);
  const label=metric.name || METRIC_NAMES[id] || id.replaceAll('_',' ');
  let value='Chưa có',unit=metric.unit;
  if(typeof metric.value==='number' && Number.isFinite(metric.value)) {
    if(['ratio','ratio_per_year'].includes(unit)){value=num(metric.value*100);unit=unit==='ratio_per_year'?'% / năm':'%';}
    else if(unit==='VND' && Math.abs(metric.value)>=1e9){value=num(metric.value/1e9);unit='Tỷ VND';}
    else value=num(metric.value,['VND','VND/share','VND/USD','shares'].includes(unit)?0:2);
  }
  unit=({'x':'Lần','shares':'Cổ phiếu','VND/share':'VND / cổ phiếu','ratio':'%','ratio_per_year':'% / năm'})[unit] || unit;
  return {label,value,unit,period:displayDate(metric.period_start)+(metric.period_start===metric.period_end?'':' – '+displayDate(metric.period_end))};
}
export function investorOverview(analysis) {
  if(!analysis)return null;
  const d=buildDashboardData(analysis),r=analysis.request,company=analysis.modules.company;
  const blocked=Object.entries(analysis.modules).filter(([,m])=>m.status==='error').map(([name])=>MODULE_NAMES[name]);
  const pending=Object.entries(analysis.modules).filter(([,m])=>m.status==='pending').map(([name])=>MODULE_NAMES[name]);
  const reasons=[];
  if(blocked.length)reasons.push('Cần xử lý lỗi: '+blocked.join(', ')+'.');
  if(pending.length)reasons.push('Chưa nhận dữ liệu: '+pending.join(', ')+'.');
  if(!d.periods.length)reasons.push('Chưa có BCTC '+BASIS_NAMES[d.frequency]+' '+(d.scope==='consolidated'?'hợp nhất':'riêng lẻ')+' đã xác minh và công bố trước ngày chốt.');
  if(!d.prices.length)reasons.push('Chưa có chuỗi giá trong kỳ yêu cầu.');
  const gap=d.prices.length>0 && Date.parse(d.prices[0].date)-Date.parse(r.period_start)>7*86400000;
  if(gap)reasons.push('Giá bắt đầu từ '+displayDate(d.prices[0].date)+'; không có dữ liệu cho phần đầu kỳ yêu cầu.');
  if(d.adjustmentBases.includes('provider_adjusted_unspecified'))reasons.push('Chưa xác minh điều chỉnh cổ tức/chia tách; biến động giá chỉ để tham khảo.');
  const missingRules=(analysis.modules.strategy.data.rules || []).filter(rule=>rule.status==='insufficient_data');
  if(missingRules.length)reasons.push(missingRules.length+' / '+(analysis.modules.strategy.data.rules || []).length+' trụ cột chiến lược còn thiếu đầu vào.');
  if(!analysis.conclusion_usable && !reasons.length)reasons.push('Còn cảnh báo hoặc bằng chứng chưa đủ điều kiện tại ngày chốt. Xem chi tiết kiểm tra dữ liệu.');
  const annual=buildDashboardData({...analysis,request:{...r,financial_basis:'annual'}}).periods;
  return {data:d,reasons,gap,blocked,pending,annualAvailable:d.frequency!=='annual' && annual.length>0,
    missingRules:missingRules.length,pricePeriod:d.prices.length?displayDate(d.prices[0].date)+' – '+displayDate(d.prices.at(-1).date):'Chưa có giá',
    financialPeriod:d.periods.length?d.periods.map(p=>displayDate(p.end)).join(' · '):'Chưa có kỳ phù hợp',
    financialLabel:(BASIS_NAMES[d.frequency] || d.frequency)+' · '+(d.scope==='consolidated'?'Hợp nhất':'Riêng lẻ'),
    companyStatus:company.status};
}
