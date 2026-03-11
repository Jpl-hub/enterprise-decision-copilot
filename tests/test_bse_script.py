from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_bse_official_reports.py"
SPEC = importlib.util.spec_from_file_location("fetch_bse_official_reports", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(MODULE)



def test_pick_full_annual_report_ignores_summary_and_picks_latest() -> None:
    rows = [
        {
            "disclosureTitle": "[定期报告]诺思兰德:2024年年度报告摘要",
            "publishDate": "2025-04-23",
            "destFilePath": "/summary.pdf",
        },
        {
            "disclosureTitle": "[定期报告]诺思兰德:2024年年度报告",
            "publishDate": "2025-04-23",
            "destFilePath": "/full.pdf",
        },
        {
            "disclosureTitle": "[临时公告]诺思兰德:2024年年度报告业绩说明会预告公告",
            "publishDate": "2025-04-23",
            "destFilePath": "/noise.pdf",
        },
    ]

    picked = MODULE.pick_full_annual_report(rows, 2024)

    assert picked is not None
    assert picked["destFilePath"] == "/full.pdf"



def test_parse_jsonp_extracts_first_payload_object() -> None:
    payload = MODULE._parse_jsonp('jsonp([{"status": 0, "listInfo": {"content": []}}])')
    assert payload["status"] == 0
    assert payload["listInfo"]["content"] == []
