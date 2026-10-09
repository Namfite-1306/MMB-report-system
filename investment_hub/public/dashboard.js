// Shared by the browser dashboard and the printable report. No external chart dependency.
const escape = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const numeric = v => typeof v === 'number' && Number.isFinite(v);
const number = (v,digits=0) => numeric(v) ? new Intl.NumberFormat('vi-VN',{maximumFractionDigits:digits}).format(v) : 'Chưa có';
export const RANGES = {all:'Tất cả',m1:'1 tháng',m3:'3 tháng',m6:'6 tháng',y1:'1 năm'};
export function buildDashboardData(analysis,range='all') {
  const request=analysis?.request || {};
  const company=analysis?.modules?.company || {data:{},sources:[]};
  const full=(company.data.price_series || []).filter(r=>r.date>=request.period_start && r.date<=request.period_end && r.date<=request.as_of_date)
    .map(r=>({...r,close:numeric(r.close)?r.close:null,volume:numeric(r.volume)&&r.volume>=0?r.volume:null})).sort((a,b)=>a.date.localeCompare(b.date));
  const withMA=full.map((r,i)=>{
    const window=full.slice(Math.max(0,i-19),i+1);
    return {...r,ma20:window.length===20 && window.every(p=>p.close!==null) ? window.reduce((sum,p)=>sum+p.close,0)/20 : null};
  });
  let start=request.period_start;
  if(range!=='all' && full.length) {
    const months={m1:1,m3:3,m6:6,y1:12}[range];
    if(months) {
      const end=new Date(full.at(-1).date+'T00:00:00Z'),day=end.getUTCDate();
      end.setUTCDate(1);end.setUTCMonth(end.getUTCMonth()-months);
      end.setUTCDate(Math.min(day,new Date(Date.UTC(end.getUTCFullYear(),end.getUTCMonth()+1,0)).getUTCDate()));
      start=end.toISOString().slice(0,10);
    }
  }
  const prices=withMA.filter(p=>p.date>=start),valid=prices.filter(p=>p.close!==null);
  const first=valid[0],last=valid.at(-1),sourceMap=new Map(company.sources.map(s=>[s.source_id,s]));
  const frequency=request.financial_basis || 'annual',scope=request.statement_scope || 'consolidated';
  const financials=(company.data.financials || []).filter(r=>r.verified===true && r.frequency===frequency && r.unit==='VND'
    && r.statement_scope===scope && r.period_end<=request.as_of_date
    && r.source_refs?.length && r.source_refs.every(ref=>{const s=sourceMap.get(ref);return s?.publication_date_verified && s.published_at && s.published_at.slice(0,10)<=request.as_of_date;}));
  const groups=new Map();
  for(const r of financials) {
    if(!['revenue','net_profit','cfo'].includes(r.item_id))continue;
    const key=r.period_start+'/'+r.period_end;
    if(!groups.has(key))groups.set(key,{start:r.period_start,end:r.period_end,values:{}});
    groups.get(key).values[r.item_id]=numeric(r.value)?r.value:null;
  }
  return {prices,periods:[...groups.values()].sort((a,b)=>a.end.localeCompare(b.end)).slice(-3),frequency,scope,
    summary:{first,last,count:valid.length,change:first?.close>0 && last ? (last.close/first.close-1)*100:null,
      low:valid.length?Math.min(...valid.map(r=>r.close)):null,high:valid.length?Math.max(...valid.map(r=>r.close)):null},
    adjustmentBases:[...new Set(prices.map(r=>r.adjustment_basis))]};
}
function svgFrame(title,body) {
  return `<svg viewBox="0 0 680 260" role="img" aria-label="${escape(title)}"><title>${escape(title)}</title>${body}</svg>`;
}
function axes(min,max,first,last,unit) {
  let result='';
  for(let i=0;i<=4;i++) {
    const y=24+i*46,value=max-(max-min)*i/4;
    result+=`<line class="chart-grid" x1="66" x2="660" y1="${y}" y2="${y}"/><text class="chart-label" x="58" y="${y+4}" text-anchor="end">${number(value,1)}</text>`;
  }
  return result+`<text class="chart-label" x="66" y="244">${escape(first || '')}</text><text class="chart-label" x="660" y="244" text-anchor="end">${escape(last || '')}</text><text class="chart-label" x="66" y="13">${escape(unit)}</text>`;
}
function bounds(values,zero=false) {
  let min=Math.min(...values),max=Math.max(...values);
  if(zero){min=Math.min(0,min);max=Math.max(0,max);}
  const padding=(max-min || Math.abs(max)*.05 || 1)*.08;
  return {min:zero&&min===0?0:min-padding,max:max+padding};
}
export function priceChart(data) {
  if(!data.prices.some(p=>p.close!==null))return '<p class="dashboard-empty">Chưa có chuỗi giá trong kỳ được chọn.</p>';
  const points=data.prices,values=points.flatMap(p=>[p.close,p.ma20].filter(numeric));
  const {min,max}=bounds(values),begin=Date.parse(points[0].date),span=Date.parse(points.at(-1).date)-begin;
  const x=r=>span?66+(Date.parse(r.date)-begin)/span*594:363,y=v=>208-(v-min)/(max-min)*184;
  function line(key,cls) {
    let d='',active=false;
    for(const p of points){if(p[key]===null){active=false;continue;}d+=(active?'L':'M')+x(p).toFixed(2)+','+y(p[key]).toFixed(2)+' ';active=true;}
    return `<path class="${cls}" d="${d}"/>`;
  }
  let body=axes(min,max,points[0].date,points.at(-1).date,'VND / cổ phiếu')+line('close','chart-price')+line('ma20','chart-ma');
  for(const p of points.filter(r=>r.close!==null))body+=`<circle class="chart-point" cx="${x(p)}" cy="${y(p.close)}" r="4"><title>${escape(p.date)} · ${number(p.close)} VND${p.ma20!==null?' · MA20 '+number(p.ma20):''}</title></circle>`;
  return svgFrame('Lịch sử giá đóng cửa và đường trung bình 20 phiên',body);
}
export function volumeChart(data) {
  if(!data.prices.some(p=>p.volume!==null))return '<p class="dashboard-empty">Chưa có khối lượng giao dịch.</p>';
  const points=data.prices,max=Math.max(...points.map(p=>p.volume || 0)) || 1;
  const begin=Date.parse(points[0].date),span=Date.parse(points.at(-1).date)-begin;
  let body=axes(0,max/1e6,points[0].date,points.at(-1).date,'Triệu cổ phiếu');
  const w=Math.max(.7,Math.min(16,500/points.length));
  for(const p of points.filter(r=>r.volume!==null)) {
    const x=span?66+(Date.parse(p.date)-begin)/span*594:363,h=p.volume/max*184;
    body+=`<rect class="chart-volume" x="${x-w/2}" y="${208-h}" width="${w}" height="${h}"><title>${escape(p.date)} · ${number(p.volume)} cổ phiếu</title></rect>`;
  }
  return svgFrame('Khối lượng giao dịch theo phiên',body);
}
export function financialChart(data) {
  const keys=['revenue','net_profit','cfo'],values=data.periods.flatMap(p=>keys.map(k=>p.values[k]).filter(numeric));
  if(!values.length)return '<p class="dashboard-empty">Chưa có BCTC đúng kỳ, phạm vi và nguồn đã xác minh để vẽ biểu đồ.</p>';
  const {min,max}=bounds(values.map(v=>v/1e9),true),y=v=>208-(v-min)/(max-min)*184,zero=y(0);
  let body=axes(min,max,'','','Tỷ VND')+`<line class="chart-zero" x1="66" x2="660" y1="${zero}" y2="${zero}"/>`;
  const groupWidth=594/data.periods.length,barWidth=Math.min(42,groupWidth/5);
  data.periods.forEach((p,i)=>{
    const center=66+groupWidth*(i+.5);
    keys.forEach((k,j)=>{const value=p.values[k];if(!numeric(value))return;
      const top=y(value/1e9),x=center+(j-1)*barWidth*1.25-barWidth/2;
      body+=`<rect class="chart-finance-${j}" x="${x}" y="${Math.min(top,zero)}" width="${barWidth}" height="${Math.abs(top-zero)}"><title>${escape(p.start+' → '+p.end)} · ${escape(k)}: ${number(value)} VND</title></rect>`;
    });
    body+=`<text class="chart-label" x="${center}" y="244" text-anchor="middle">${escape(p.end)}</text>`;
  });
  return svgFrame('Doanh thu, lợi nhuận sau thuế và dòng tiền kinh doanh theo kỳ BCTC',body);
}
export function dashboardMarkup(analysis,{range='all',interactive=true}={}) {
  if(!analysis)return '<div class="dashboard-empty">Tạo hoặc mở lần phân tích để xem dashboard từ dữ liệu của nhóm.</div>';
  const data=buildDashboardData(analysis,range),s=data.summary;
  const card=(label,value,note)=>`<article class="dashboard-stat"><span>${label}</span><strong>${value}</strong><small>${escape(note)}</small></article>`;
  const change=numeric(s.change)?`${s.change>0?'+':''}${number(s.change,2)}%`:'Chưa có';
  const controls=interactive?`<div class="dashboard-range" role="group" aria-label="Khoảng thời gian biểu đồ">${Object.entries(RANGES).map(([key,label])=>`<button type="button" data-range="${key}" aria-pressed="${key===range}">${label}</button>`).join('')}</div>`:'';
  const priceNote=`${data.prices[0]?.date || 'Chưa có'} → ${data.prices.at(-1)?.date || 'Chưa có'} · ${s.count} phiên có giá`;
  const kind={annual:'Năm',ytd:'Lũy kế',quarterly:'Quý',ttm:'TTM'}[data.frequency] || data.frequency;
  return `<div class="dashboard-stats">${card('Đóng cửa gần nhất',number(s.last?.close)+' <em>VND</em>',s.last?.date || 'Chưa có phiên giá')}${card('Thay đổi giá trong kỳ',change,'Giá cuối / giá đầu − 1')}${card('Khoảng giá đóng cửa',number(s.low)+' – '+number(s.high),'VND / cổ phiếu')}${card('Khối lượng phiên cuối',number(s.last?.volume),s.last?.date || 'Cổ phiếu')}</div>
    <article class="chart-card chart-main"><div class="chart-head"><div><p class="chart-eyebrow">MARKET OVERVIEW · ${escape(analysis.request.ticker)}</p><h3>Lịch sử giá</h3><p>${escape(priceNote)}</p></div>${controls}</div><div class="chart-legend"><span class="legend-price">Đóng cửa</span><span class="legend-ma">MA20</span></div>${priceChart(data)}<p class="chart-note">MA20 = trung bình 20 phiên có trong dữ liệu, chỉ dùng giá tới phiên đang tính; không lấp ngày nghỉ hoặc giá thiếu. Cơ sở điều chỉnh: ${escape(data.adjustmentBases.join(', ') || 'Chưa có')}. Thay đổi giá chưa bao gồm cổ tức và chi phí giao dịch.</p></article>
    <div class="dashboard-chart-grid"><article class="chart-card"><div class="chart-head"><div><p class="chart-eyebrow">TRADING ACTIVITY</p><h3>Khối lượng giao dịch</h3><p>${escape(priceNote)}</p></div></div>${volumeChart(data)}<p class="chart-note">Mỗi cột là một phiên, đơn vị triệu cổ phiếu; dữ liệu thiếu không thay bằng 0.</p></article><article class="chart-card"><div class="chart-head"><div><p class="chart-eyebrow">FINANCIAL PERFORMANCE</p><h3>Kết quả kinh doanh</h3><p>${escape(kind)} · ${escape(data.scope==='consolidated'?'Hợp nhất':'Riêng lẻ')} · ${data.periods.length} kỳ</p></div></div><div class="chart-legend"><span class="legend-price">Doanh thu</span><span class="legend-volume">LN sau thuế</span><span class="legend-ma">CFO</span></div>${financialChart(data)}<p class="chart-note">Chỉ dùng BCTC đã đối chiếu, cùng tần suất/phạm vi, công bố trước ngày chốt. Giữ dấu âm của dòng tiền; không quy đổi YTD thành năm.</p></article></div>`;
}
