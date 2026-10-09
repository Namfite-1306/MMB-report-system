"""Reproduce the normalized transcription of visually checked issuer PDFs.

This is a fixed, dated evidence snapshot, not a provider for arbitrary tickers.
PDF physical page numbers are retained; no numbers are generated or interpolated.
"""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
RAW=HERE/'hpg_raw'
bundle={'ticker':'HPG','sources':[],'financials':[],'price_series':[],'news':[], 'warnings':[
    'BCTC bán niên 2026 phân loại lại số đầu kỳ; không suy luận tăng trưởng TSNH/tồn kho giữa hai cách phân loại.',
    'EPS năm 2025 và H1/2026 chưa đối chiếu điều chỉnh cổ phiếu 2026; P/E giữ null.',
    'Ngày công bố issuer FY2025=2026-03-27/H1-2026=2026-08-28; API publicDate=2026-03-30/2026-09-03.',
    'Ảnh PDF năm 2025 xác nhận LNST 15.514.931.571.606 VND; không dùng bản OCR chưa kiểm.']}

for doc,pub,title,pages in [
    ('annual_pdf','2026-03-27','BCTC hợp nhất kiểm toán HPG 2025',{'bs_assets':8,'bs_current':7,'bs_funding':9,'income':10,'cashflow':11}),
    ('interim_pdf','2026-08-28','BCTC hợp nhất soát xét HPG 6 tháng 2026',{'bs_assets':10,'bs_current':9,'bs_funding':11,'income':12,'cashflow':13})]:
    meta=json.loads((RAW/(doc+'.meta.json')).read_text(encoding='utf-8'))
    for section,page in pages.items():
        bundle['sources'].append({'source_id':f'company_src_{doc}_{section}','title':title+' - '+section,
            'url':meta['url'],'published_at':pub,'retrieved_at':meta['retrieved_at'],
            'locator':f'Trang PDF {page}; trang in {page-(2 if doc=="annual_pdf" else 4)}; VND; cột kỳ này/kỳ trước',
            'publication_date_verified':True,'verification_method':'Đối chiếu ảnh PDF và ngày đăng trên trang issuer',
            'publication_evidence_url':'https://www.hoaphat.com.vn/quan-he-co-dong/bao-cao-tai-chinh',
            'raw_file':f'hpg_raw/{doc}.pdf','raw_sha256':meta['sha256']})

def add(doc,section,start,end,freq,values):
    for item,value in values.items():
        bundle['financials'].append({'record_id':f'company_pdf_{doc}_{start}_{end}_{item}',
            'item_id':item,'value':value,'unit':'VND/share' if item=='basic_eps' else 'VND','frequency':freq,
            'period_start':start,'period_end':end,'statement_scope':'consolidated',
            'source_refs':[f'company_src_{doc}_{section}'],'verified':True,'verification_method':'read_pdf_visual'})

for date,vals in [('2025-12-31',(103659402759724,8300890304205,52828227344442)),
                  ('2024-12-31',(86674276272995,6887646139852,46091222189472))]:
    add('annual_pdf','bs_current',date,date,'point_in_time',dict(zip(('current_assets','cash','inventory'),vals)))
for date,value in [('2025-12-31',257899200817547),('2024-12-31',224489707553981)]:
    add('annual_pdf','bs_assets',date,date,'point_in_time',{'assets':value})
funding=('liabilities','current_liabilities','short_debt','long_debt','equity_total','noncontrolling_interest')
for date,vals in [('2025-12-31',(126679189940972,94186268324508,64694957245143,27479194057074,131220010876575,2039012776403)),
                  ('2024-12-31',(109842249570282,75225243262689,55882686213459,27080443256096,114647457983699,290990632368))]:
    add('annual_pdf','bs_funding',date,date,'point_in_time',dict(zip(funding,vals)))
income=('revenue','gross_profit','interest_expense','pretax_profit','net_profit','parent_profit','basic_eps')
for year,vals in [(2025,(156116094618482,24497788183182,3114855868974,18040591977880,15514931571606,15453174006223,1973)),
                  (2024,(138855112131387,18497549127684,2287360810880,13693502261178,12020023621271,12021443836074,1505))]:
    add('annual_pdf','income',f'{year}-01-01',f'{year}-12-31','annual',dict(zip(income,vals)))
for year,c,k in [(2025,17365859056591,-25748320476719),(2024,6608320655215,-35495026797327)]:
    add('annual_pdf','cashflow',f'{year}-01-01',f'{year}-12-31','annual',{'cfo':c,'capex_cash':k})
add('interim_pdf','bs_current','2026-06-30','2026-06-30','point_in_time',{'current_assets':119968988853207,'cash':9782057360909,'inventory':55607877088316})
add('interim_pdf','bs_assets','2026-06-30','2026-06-30','point_in_time',{'assets':278929786247772})
add('interim_pdf','bs_funding','2026-06-30','2026-06-30','point_in_time',dict(zip(funding,(137413759457075,105037075079739,71433383400905,27096593831648,141516026790697,859680276468))))
for year,vals in [(2026,(108059749601554,18852855801426,2853028567414,17946868046971,15480392467117,15365022248705,1781)),
                  (2025,(73532193664787,12013876410841,1066136992112,8812148842683,7614329521616,7600771906152,880))]:
    add('interim_pdf','income',f'{year}-01-01',f'{year}-06-30','ytd',dict(zip(income,vals)))
for year,c,k in [(2026,12641697117285,-12523577829074),(2025,507162083475,-10688184320479)]:
    add('interim_pdf','cashflow',f'{year}-01-01',f'{year}-06-30','ytd',{'cfo':c,'capex_cash':k})

def write(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
write(HERE/'hpg_verified.json',bundle)
request={'schema_version':'1.0','run_id':'run_hpg_company_20261009_v1','ticker':'HPG','exchange':'HOSE',
    'industry_code':'1750','industry_name':'Sản xuất Thép & Kim loại','as_of_date':'2026-10-09',
    'period_start':'2025-01-01','period_end':'2026-10-08',
    'investment_horizon':'6–12 tháng (cấu hình chạy thử; người 5 thay bằng lựa chọn người dùng)',
    'language':'vi','currency':'VND','financial_basis':'ytd','statement_scope':'consolidated'}
write(HERE/'request.hpg.json',request)
request['financial_basis']='annual'
write(HERE/'request.hpg.annual.json',request)
print('Verified financial records:',len(bundle['financials']))
