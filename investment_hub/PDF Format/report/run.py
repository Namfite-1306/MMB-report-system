"""MMB Analysis PDF adapter: one JSON on stdin, one JSON on stdout."""
import json
import sys
from pathlib import Path
from src.pdf_generator import generate_pdf


def main():
    payload = json.load(sys.stdin)
    directory = Path(payload['output_dir'])
    if not directory.is_absolute():
        raise ValueError('output_dir phải là đường dẫn tuyệt đối do hệ thống cấp.')
    analysis = payload['analysis']
    if not analysis.get('run_id') or not analysis.get('request', {}).get('ticker'):
        raise ValueError('Adapter cần analysis thật từ hệ thống, có run_id và ticker.')
    manifest = generate_pdf(analysis, directory / 'report.pdf', directory / 'report_manifest.json')
    print(json.dumps({'pdf_filename': 'report.pdf', 'manifest': manifest}, ensure_ascii=False))


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    try:
        main()
    except Exception as exc:
        print('PDF: ' + str(exc), file=sys.stderr)
        sys.exit(1)
