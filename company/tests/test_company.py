"""Kiểm tra các rủi ro dữ liệu ảnh hưởng kết quả, không cần mạng."""
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from company.analyzer import analyze_company
from company.contract import validate_request, validate_company_output, envelope
from company.metrics import calculate_metrics
from company.providers import load_snapshot

ROOT=Path(__file__).resolve().parents[1]
EXAMPLES=ROOT/'examples'

def request():
    return {'schema_version':'1.0','run_id':'test_shared_run','ticker':'HPG','exchange':'HOSE',
            'industry_code':'1750','industry_name':'Thép','as_of_date':'2026-10-09',
            'period_start':'2025-01-01','period_end':'2026-10-08','investment_horizon':'12 tháng',
            'language':'vi','currency':'VND','financial_basis':'annual'}

def source(sid='company_src_test',pub='2026-03-27',verified=True):
    return {'source_id':sid,'title':'TEST FIXTURE, không phải số liệu nghiên cứu','url':'https://example.org/fixture',
            'published_at':pub,'retrieved_at':'2026-10-09T14:00:00+07:00','locator':'test',
            'publication_date_verified':verified}

def financial(item,value,start='2025-01-01',end='2025-12-31',freq='annual',**kwargs):
    return {'record_id':f'company_test_{item}_{start}_{end}_{kwargs.get("tag", "a")}',
            'item_id':item,'value':value,'unit':'VND','period_start':start,'period_end':end,
            'frequency':freq,'statement_scope':'consolidated','verified':True,'source_refs':['company_src_test'],
            **{k:v for k,v in kwargs.items() if k!='tag'}}

def metrics(rows,req=None,sources=None,prices=None):
    result,_=calculate_metrics(req or request(),rows,prices or [],sources or [source()])
    return {r['metric_id']:r for r in result}

class FormulaTests(unittest.TestCase):
    def test_missing_is_null(self):
        self.assertIsNone(metrics([])['company_roa']['value'])

    def test_zero_denominator(self):
        rows=[financial('revenue',0),financial('gross_profit',3)]
        self.assertIsNone(metrics(rows)['company_gross_margin']['value'])

    def test_actual_zero_not_missing(self):
        rows=[financial('revenue',10),financial('net_profit',0)]
        self.assertEqual(metrics(rows)['company_net_margin']['value'],0)

    def test_ratios_decimal(self):
        rows=[financial('revenue',100),financial('gross_profit',20)]
        self.assertAlmostEqual(metrics(rows)['company_gross_margin']['value'],.2)

    def test_roa_average_assets(self):
        rows=[financial('revenue',100),financial('net_profit',20),
              financial('assets',100,'2024-12-31','2024-12-31','point_in_time'),
              financial('assets',300,'2025-12-31','2025-12-31','point_in_time')]
        self.assertAlmostEqual(metrics(rows)['company_roa']['value'],.1)

    def test_roe_parent_average_excludes_minority(self):
        rows=[financial('revenue',100),financial('parent_profit',20)]
        for date,e,n in [('2024-12-31',110,10),('2025-12-31',330,30)]:
            rows += [financial('equity_total',e,date,date,'point_in_time'),financial('noncontrolling_interest',n,date,date,'point_in_time')]
        self.assertAlmostEqual(metrics(rows)['company_roe']['value'],.1)

    def test_roa_does_not_fallback_to_end_balance(self):
        rows=[financial('revenue',100),financial('net_profit',20),financial('assets',300,'2025-12-31','2025-12-31','point_in_time')]
        self.assertIsNone(metrics(rows)['company_roa']['value'])

    def test_future_publication_excluded(self):
        self.assertIsNone(metrics([financial('revenue',100)],sources=[source(pub='2026-10-10')])['company_revenue']['value'])

    def test_unknown_publication_excluded(self):
        self.assertIsNone(metrics([financial('revenue',100)],sources=[source(pub=None,verified=False)])['company_revenue']['value'])

    def test_unverified_scope_excluded(self):
        rows=[financial('revenue',100,statement_scope='unknown',verified=False)]
        self.assertIsNone(metrics(rows)['company_revenue']['value'])

    def test_scopes_not_mixed(self):
        rows=[financial('revenue',100),financial('net_profit',20,statement_scope='separate')]
        self.assertIsNone(metrics(rows)['company_net_margin']['value'])

    def test_quarter_not_used_as_annual(self):
        rows=[financial('revenue',100,'2025-04-01','2025-06-30','quarterly')]
        self.assertIsNone(metrics(rows)['company_revenue']['value'])

    def test_ytd_no_annualization(self):
        req=request();req['financial_basis']='ytd'
        rows=[financial('revenue',100,'2025-01-01','2025-06-30','ytd'),financial('net_profit',10,'2025-01-01','2025-06-30','ytd')]
        self.assertEqual(metrics(rows,req)['company_net_profit']['value'],10)

    def test_growth_negative_base_null(self):
        rows=[financial('revenue',100),financial('parent_profit',20),financial('parent_profit',-10,'2024-01-01','2024-12-31')]
        self.assertIsNone(metrics(rows)['company_parent_profit_growth_yoy']['value'])

    def test_fcf_cash_sign(self):
        rows=[financial('revenue',100),financial('cfo',25),financial('capex_cash',-30)]
        self.assertEqual(metrics(rows)['company_free_cash_flow']['value'],-5)

    def test_positive_capex_rejected(self):
        rows=[financial('revenue',100),financial('cfo',25),financial('capex_cash',30)]
        self.assertIsNone(metrics(rows)['company_free_cash_flow']['value'])

    def test_total_liabilities_not_debt(self):
        date='2025-12-31';rows=[financial('assets',200,date,date,'point_in_time')]
        for item,value in [('liabilities',100),('short_debt',20),('long_debt',30),('equity_total',100)]:
            rows.append(financial(item,value,date,date,'point_in_time'))
        self.assertEqual(metrics(rows)['company_debt_to_equity']['value'],.5)

    def test_bank_liquidity_not_generalized(self):
        req=request();req['industry_code']='8350'
        date='2025-12-31';rows=[financial(item,value,date,date,'point_in_time') for item,value in [('assets',200),('current_assets',100),('current_liabilities',50)]]
        self.assertIsNone(metrics(rows,req)['company_current_ratio']['value'])

    def test_ttm_contiguous_quarters(self):
        req=request();req['financial_basis']='ttm'
        periods=[('2025-01-01','2025-03-31'),('2025-04-01','2025-06-30'),('2025-07-01','2025-09-30'),('2025-10-01','2025-12-31')]
        rows=[financial('revenue',100,s,e,'quarterly') for s,e in periods]
        result=metrics(rows,req)
        self.assertEqual(result['company_revenue']['value'],400)
        self.assertEqual(len(result['company_revenue']['input_refs']),4)

    def test_ttm_missing_quarter(self):
        req=request();req['financial_basis']='ttm'
        rows=[financial('revenue',100,'2025-01-01','2025-03-31','quarterly')]
        self.assertIsNone(metrics(rows,req)['company_revenue']['value'])

    def test_ttm_never_sum_ytd_eps(self):
        req=request();req['financial_basis']='ttm'
        rows=[financial('revenue',100,'2025-01-01','2025-06-30','ytd'),financial('basic_eps',5,'2025-01-01','2025-06-30','ytd')]
        self.assertIsNone(metrics(rows,req)['company_basic_eps']['value'])

    def test_conflicting_same_version_null(self):
        rows=[financial('revenue',100),financial('revenue',110,tag='b')]
        self.assertIsNone(metrics(rows)['company_revenue']['value'])

    def test_unknown_price_basis_no_pe(self):
        prices=[{'date':'2026-10-08','close':20,'volume':100,'source_refs':['company_src_test'],'adjustment_basis':'unknown'}]
        rows=[financial('revenue',100),financial('basic_eps',2)]
        self.assertIsNone(metrics(rows,prices=prices)['company_pe']['value'])

    def test_verified_price_pe(self):
        prices=[{'date':'2026-10-08','close':20,'volume':100,'source_refs':['company_src_test'],'adjustment_basis':'unadjusted','basis_verified':True}]
        rows=[financial('revenue',100),financial('basic_eps',2,per_share_basis_verified=True,share_basis_valid_through='2026-10-08')]
        self.assertEqual(metrics(rows,prices=prices)['company_pe']['value'],10)

    def test_spot_alone_not_enough_if_eps_share_basis_unknown(self):
        prices=[{'date':'2026-10-08','close':20,'volume':100,'source_refs':['company_src_test'],'adjustment_basis':'unadjusted','basis_verified':True}]
        rows=[financial('revenue',100),financial('basic_eps',2)]
        self.assertIsNone(metrics(rows,prices=prices)['company_pe']['value'])

    def test_historical_adjusted_snapshot_not_known_at_cutoff(self):
        req=request();req['as_of_date']='2025-12-31';req['period_end']='2025-12-31'
        prices=[{'date':'2025-12-30','close':20,'volume':100,'source_refs':['company_src_test'],'adjustment_basis':'provider_adjusted_unspecified'}]
        self.assertIsNone(metrics([],req,sources=[source(pub='2025-12-30')],prices=prices)['company_close']['value'])

class ContractTests(unittest.TestCase):
    def test_valid_request(self): validate_request(request())
    def test_missing_horizon(self):
        req=request();req.pop('investment_horizon')
        with self.assertRaises(ValueError):validate_request(req)
    def test_bad_dates(self):
        req=request();req['period_end']='2026-10-10'
        with self.assertRaises(ValueError):validate_request(req)
    def test_invalid_calendar(self):
        req=request();req['period_end']='2026-02-30'
        with self.assertRaises(ValueError):validate_request(req)
    def test_invalid_request_envelope(self):
        doc=analyze_company({'ticker':'HPG'})
        self.assertEqual(doc['status'],'error');self.assertIn('sources',doc)
    def test_pending_full_structure(self):
        doc=analyze_company(request(),pending=True)
        self.assertEqual(doc['status'],'pending');self.assertTrue(validate_company_output(doc)[0])
    def test_snapshot_hash_tampering(self):
        with tempfile.TemporaryDirectory() as path:
            p=Path(path);(p/'prices.json').write_text('[]');(p/'prices.meta.json').write_text('{"sha256":"wrong"}')
            _,errors=load_snapshot(p)
            self.assertTrue(any('SHA256' in e for e in errors))

class RealSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        req=json.loads((EXAMPLES/'request.hpg.json').read_text(encoding='utf-8'))
        cls.doc=analyze_company(req,snapshot_dir=EXAMPLES/'hpg_raw',verified_bundle=EXAMPLES/'hpg_verified.json')
        cls.m={m['metric_id']:m for m in cls.doc['data']['metrics']}
    def test_contract_and_partial(self):
        self.assertTrue(validate_company_output(self.doc)[0]);self.assertEqual(self.doc['status'],'partial')
    def test_real_net_revenue_not_sales(self):
        self.assertEqual(self.m['company_revenue']['value'],108059749601554)
    def test_real_ytd_roa(self):
        self.assertAlmostEqual(self.m['company_roa']['value'],15480392467117/((257899200817547+278929786247772)/2))
    def test_real_yoy_matching_half_year(self):
        self.assertAlmostEqual(self.m['company_revenue_growth_yoy']['value'],108059749601554/73532193664787-1)
    def test_price_not_multiplied_by_1000(self):
        self.assertEqual(self.doc['data']['price_series'][-1]['close'],20150)
    def test_no_zero_for_unverified_valuation(self):
        for key in ('company_pe','company_pb','company_market_cap'):self.assertIsNone(self.m[key]['value'])
    def test_raw_not_used_for_metrics(self):
        for m in self.doc['data']['metrics']:
            for ref in m['input_refs']:self.assertNotIn('company_vci_',ref)
    def test_deterministic_replay(self):
        req=json.loads((EXAMPLES/'request.hpg.json').read_text(encoding='utf-8'))
        other=analyze_company(req,snapshot_dir=EXAMPLES/'hpg_raw',verified_bundle=EXAMPLES/'hpg_verified.json')
        self.assertEqual(other['data'],self.doc['data'])

if __name__=='__main__':unittest.main()
