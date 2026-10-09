"""Software-only fixtures; all values are missing except explicit zero/decimal test cases."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
from pdf_generator import generate_pdf, safe_conclusion, validate_analysis, SECTIONS
from pypdf import PdfReader


def fixture():
    data = json.loads((ROOT / 'inputs/pending_analysis.json').read_text(encoding='utf-8'))
    data['run_id'] = '11111111-1111-4111-8111-111111111111'
    data['request'].update(ticker='TST', as_of_date='2026-10-09',
                           industry_name='KIỂM THỬ PHẦN MỀM - KHÔNG PHẢI DỮ LIỆU ĐẦU TƯ',
                           period_start='2025-01-01', period_end='2025-12-31')
    for module in data['modules'].values():
        module.update(run_id=data['run_id'], ticker='TST', as_of_date='2026-10-09')
    data['conclusion_usable'] = False
    data['display_conclusion'] = {'label': 'insufficient_data', 'rationale': 'Chưa đủ bằng chứng.',
                                  'horizon': 'Test only', 'evidence_refs': []}
    return data


class PdfTests(unittest.TestCase):
    def test_blocked_conclusion_never_uses_raw_recommendation(self):
        data = fixture()
        data['modules']['strategy']['data']['conclusion'] = {
            'label': 'attractive', 'rationale': 'RAW_UNSAFE_SHOULD_NOT_APPEAR'}
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / 'report.pdf'
            manifest = generate_pdf(data, filename)
            content = '\n'.join(p.extract_text() for p in PdfReader(filename).pages)
            self.assertIn('Chưa đủ bằng chứng', content)
            self.assertNotIn('RAW_UNSAFE_SHOULD_NOT_APPEAR', content)
            self.assertEqual(set(manifest['sections_present']), set(SECTIONS))
            self.assertEqual(manifest['conclusion_label'], 'insufficient_data')
        data.pop('display_conclusion')
        self.assertEqual(safe_conclusion(data)['label'], 'insufficient_data')

    def test_long_tables_literal_markup_zero_and_decimal(self):
        data = fixture()
        rows = []
        for index in range(55):
            rows.append({'metric_id': 'company:test_' + str(index), 'value': None,
                         'unit': 'ratio', 'frequency': 'year', 'period_start': '2025-01-01',
                         'period_end': '2025-12-31', 'formula_id': None, 'source_refs': []})
        rows[0]['value'] = 0
        rows[1]['value'] = 0.012345
        data['modules']['company']['data']['metrics'] = rows
        data['modules']['company']['data']['findings'] = [
            {'text': '<b>Literal & text</b>', 'evidence_refs': []}]
        data['modules']['company']['sources'] = [{
            'source_id': 'company:test', 'title': 'Synthetic test source',
            'url': 'https://example.test/' + 'long-url-' * 70,
            'published_at': None, 'retrieved_at': '2026-10-09T00:00:00+07:00',
            'publication_date_verified': False, 'locator': 'Fixture only'}]
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / 'report.pdf'
            generate_pdf(data, filename)
            reader = PdfReader(filename)
            content = '\n'.join(p.extract_text() for p in reader.pages)
            self.assertIn('0.012345', content)
            self.assertIn('<b>Literal & text</b>', content)
            self.assertIn('company:test_54', content)
            self.assertIn('Chưa có', content)
            self.assertGreater(len(reader.pages), 3)
            self.assertTrue(all(abs(float(p.mediabox.width) - 595.276) < 1 for p in reader.pages))

    def test_missing_modules_or_wrong_identity_are_rejected_without_mutation(self):
        data = fixture()
        original = copy.deepcopy(data)
        data['modules']['industry']['ticker'] = 'OTHER'
        with self.assertRaises(ValueError): validate_analysis(data)
        data = original
        del data['modules']['macro']
        with self.assertRaises(ValueError): validate_analysis(data)
        self.assertNotIn('macro', data['modules'])


if __name__ == '__main__':
    unittest.main()
