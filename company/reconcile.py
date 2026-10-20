"""So số BCTC đã đọc PDF với API; không tự sửa/verify khi thấy khớp."""
import json
from pathlib import Path
from .providers import FIELDS
from .contract import write_json

def reconcile(raw_dir, verified_bundle):
    raw_dir=Path(raw_dir)
    bundle=json.loads(Path(verified_bundle).read_text(encoding="utf-8"))
    datasets={}
    for kind in FIELDS:
        path=raw_dir/(kind+'.json')
        datasets[kind]=json.loads(path.read_text(encoding='utf-8')).get('data',{}) if path.exists() else {}
    results=[]
    for record in bundle['financials']:
        item=record['item_id']
        kind=next((k for k,fields in FIELDS.items() if item in fields),None)
        if not kind: continue
        field=FIELDS[kind][item][0]
        year=int(record['period_end'][:4]);frequency=record['frequency'];q=int(record['period_end'][5:7])//3
        table='years' if frequency=='annual' or (frequency=='point_in_time' and q==4) else 'quarters'
        rows=[r for r in datasets[kind].get(table,[]) if r.get('yearReport')==year]
        note=None
        if table=='years':rows=[r for r in rows if r.get('lengthReport')==5]
        elif frequency=='ytd' and kind in ('income','cashflow'):
            # Thuần đối chiếu các dòng tiền/thu nhập; không cộng EPS.
            rows=sorted([r for r in rows if 1<=r.get('lengthReport',0)<=q],key=lambda r:r['lengthReport'])
            if item=='basic_eps':
                note='EPS không cộng quý; API quarterly có thể đang trả EPS YTD';rows=[]
            elif len(rows)!=q or {r['lengthReport'] for r in rows}!=set(range(1,q+1)):
                note='Không đủ quý standalone cho đối chiếu';rows=[]
            else:note='Đối chiếu tổng Q1..Qn API với YTD PDF; phép đối chiếu này không xác minh bản hồi tố'
        else:
            rows=[r for r in rows if r.get('lengthReport')==q]
        values=[r.get(field) for r in rows]
        api_value=sum(values) if values and all(isinstance(v,(int,float)) for v in values) else None
        # VCI expenses âm trong khi PDF trình bày magnitude dương.
        if item=='interest_expense' and api_value is not None:
            api_value=-api_value
            note=(note+'; ' if note else '')+'Chuẩn hóa dấu chi phí lãi vay API (âm) sang magnitude PDF (dương)'
        pdf_value=record['value']
        difference=api_value-pdf_value if api_value is not None and pdf_value is not None else None
        dates=sorted({r.get('publicDate','')[:10] for r in rows if r.get('publicDate')})
        source_id=record['source_refs'][0]
        pub=next(s['published_at'] for s in bundle['sources'] if s['source_id']==source_id)
        results.append({'record_id':record['record_id'],'item_id':item,'frequency':frequency,
            'period_start':record['period_start'],'period_end':record['period_end'],
            'pdf_value':pdf_value,'api_value_normalized':api_value,'difference_api_minus_pdf':difference,
            'numeric_match':difference==0 if difference is not None else None,
            'issuer_published_at':pub,'api_public_dates':dates,'source_refs':record['source_refs'],'note':note})
    return {'ticker':bundle['ticker'],'rows':results,
        'summary':{'compared':sum(r['difference_api_minus_pdf'] is not None for r in results),
                   'exact_matches':sum(r['numeric_match'] is True for r in results),
                   'mismatches':sum(r['numeric_match'] is False for r in results)},
        'warning':'Số API khớp không tự chứng minh ngày công bố, scope hoặc bản dữ liệu đã biết ở ngày chốt. PDF là nguồn của verified bundle.'}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--raw-dir',required=True)
    parser.add_argument('--verified-bundle',required=True)
    parser.add_argument('-o','--output',default='company/reconciliation.json')
    args=parser.parse_args()
    result=reconcile(args.raw_dir,args.verified_bundle)
    write_json(args.output,result)
    print(json.dumps(result['summary'],ensure_ascii=False))
