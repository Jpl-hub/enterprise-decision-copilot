from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_official_report_inventory.py"
SPEC = importlib.util.spec_from_file_location("build_official_report_inventory", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(MODULE)



def test_build_target_coverage_counts_missing_slots() -> None:
    inventory = pd.DataFrame(
        [
            {"company_code": "300760", "year": 2022, "status": "downloaded", "file_exists": True},
            {"company_code": "300760", "year": 2023, "status": "downloaded", "file_exists": True},
            {"company_code": "300760", "year": 2024, "status": "downloaded", "file_exists": True},
            {"company_code": "300015", "year": 2022, "status": "downloaded", "file_exists": True},
        ]
    )

    original_targets_path = MODULE.TARGETS_PATH
    try:
        temp_targets = Path(__file__).resolve().parent / "tmp_targets_inventory.csv"
        temp_targets.write_text(
            "company_code,company_name,exchange\n300760,迈瑞医疗,SZSE\n300015,爱尔眼科,SZSE\n",
            encoding="utf-8",
        )
        MODULE.TARGETS_PATH = temp_targets
        coverage = MODULE.build_target_coverage(inventory)
    finally:
        MODULE.TARGETS_PATH = original_targets_path
        if temp_targets.exists():
            temp_targets.unlink()

    assert coverage["expected_slots"] == 6
    assert coverage["downloaded_slots"] == 4
    assert coverage["coverage_ratio"] == 0.6667
    assert len(coverage["missing_slots"]) == 2



def test_load_manifest_rows_normalizes_bse_fields() -> None:
    original_specs = MODULE.MANIFEST_SPECS
    try:
        temp_manifest = Path(__file__).resolve().parent / "tmp_bse_manifest.json"
        temp_manifest.write_text(
            '[{"company_code":"920047","disclosure_company_code":"430047","company_name":"诺思兰德","year":2024,"local_path":"missing.pdf","status":"downloaded"}]',
            encoding="utf-8",
        )
        MODULE.MANIFEST_SPECS = [("BSE", temp_manifest)]
        rows = MODULE.load_manifest_rows()
    finally:
        MODULE.MANIFEST_SPECS = original_specs
        if temp_manifest.exists():
            temp_manifest.unlink()

    assert len(rows) == 1
    assert rows[0]["exchange"] == "BSE"
    assert rows[0]["company_code"] == "920047"
    assert rows[0]["disclosure_company_code"] == "430047"
    assert rows[0]["file_exists"] is False
