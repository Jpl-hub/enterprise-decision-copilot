from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from PyPDF2 import PdfReader

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.llm import SiliconFlowClient

INVENTORY_PATH = ROOT / "data" / "raw" / "official" / "report_inventory.csv"
CACHE_DIR = ROOT / "data" / "cache" / "official_extract"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

KEYWORDS = {
    "company_name": ["公司名称", "证券简称"],
    "report_year": ["年度报告", "主要会计数据", "主要财务指标"],
    "revenue_million": ["营业收入", "营业总收入"],
    "net_profit_million": ["归属于上市公司股东的净利润", "归属于母公司股东的净利润"],
    "gross_margin_pct": ["毛利率"],
    "net_margin_pct": ["净利率"],
    "rd_total_million": ["研发投入合计", "本期费用化研发投入", "研发费用"],
    "rd_ratio_pct": ["研发投入总额占营业收入比例", "研发投入占营业收入比例"],
    "debt_ratio_pct": ["资产负债率"],
    "current_assets_million": ["流动资产合计"],
    "current_liabilities_million": ["流动负债合计"],
    "current_ratio": ["流动比率"],
    "monetary_funds_million": ["货币资金"],
    "short_term_debt_million": ["短期借款", "一年内到期的非流动负债"],
    "cash_to_short_debt": ["现金短债比", "现金及现金等价物/短期债务"],
    "inventory_turnover": ["存货周转率"],
    "receivable_turnover": ["应收账款周转率"],
    "operating_cashflow_million": ["经营活动产生的现金流量净额"],
    "roe_pct": ["加权平均净资产收益率"],
}

SYSTEM_PROMPT = """你是上市公司年报指标抽取助手。你只能根据用户给出的中文年报证据片段提取或推导字段，不能编造。

输出严格 JSON，字段如下：
company_code, company_name, report_year,
revenue_million, net_profit_million, gross_margin_pct, net_margin_pct,
rd_total_million, rd_ratio_pct, debt_ratio_pct,
current_assets_million, current_liabilities_million, current_ratio,
monetary_funds_million, short_term_debt_million, cash_to_short_debt,
inventory_turnover, receivable_turnover,
operating_cashflow_million, roe_pct,
field_sources, notes

规则：
1. 金额统一输出为“百万元”数值，不带单位。若原文是元，除以1000000；若原文是万元，除以10000。
2. 百分比统一输出数值，不带%。
3. current_ratio 可由 流动资产合计 / 流动负债合计 推导。
4. cash_to_short_debt 可由 货币资金 / 短期债务 推导。短期债务可使用“短期借款 + 一年内到期的非流动负债”，如果只有其中一项，按已明确可得部分推导并在 notes 说明。
5. net_margin_pct 可由 净利润 / 营业收入 * 100 推导。
6. rd_ratio_pct 可由 研发投入合计 / 营业收入 * 100 推导。
7. 如果证据不足，则填 null。
8. field_sources 是对象，键为字段名，值为使用的证据简述。
9. notes 是数组，写明推导逻辑或不确定点。
10. 不要输出任何 JSON 之外的文字。
"""



def _load_manifest_records() -> list[dict]:
    if INVENTORY_PATH.exists():
        inventory = pd.read_csv(INVENTORY_PATH, dtype={"company_code": str, "disclosure_company_code": str})
        if inventory.empty:
            return []
        inventory = inventory[(inventory["status"] == "downloaded") & (inventory["file_exists"] == True)].copy()
        return inventory.to_dict("records")

    manifest_records: list[dict] = []
    legacy_paths = [
        ROOT / "data" / "raw" / "official" / "sse" / "report_manifest.json",
        ROOT / "data" / "raw" / "official" / "szse" / "report_manifest.json",
        ROOT / "data" / "raw" / "official" / "bse" / "report_manifest.json",
    ]
    for manifest_path in legacy_paths:
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for record in manifest:
            if record.get("status") == "downloaded":
                manifest_records.append(record)
    return manifest_records
def read_pdf_pages(pdf_path: Path) -> list[str]:
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        text = (page.extract_text() or "").replace("\u2022", " ")
        pages.append(text)
    return pages


def collect_snippets(pages: list[str], max_hits_per_field: int = 3) -> dict[str, list[str]]:
    snippets: dict[str, list[str]] = {}
    for field, words in KEYWORDS.items():
        hits: list[str] = []
        for page_no, text in enumerate(pages, start=1):
            for word in words:
                idx = text.find(word)
                if idx == -1:
                    continue
                snippet = text[max(0, idx - 120) : idx + 360].replace("\n", " ").strip()
                hits.append(f"[page {page_no}] {snippet}")
                break
            if len(hits) >= max_hits_per_field:
                break
        snippets[field] = hits
    return snippets


def build_user_prompt(record: dict, snippets: dict[str, list[str]]) -> str:
    lines = [
        f"company_code: {record['company_code']}",
        f"report_year_target: {record['year']}",
        f"source_url: {record['source_url']}",
        "以下是从官方年报 PDF 中提取的证据片段：",
    ]
    for field, values in snippets.items():
        lines.append(f"\n## {field}")
        if values:
            lines.extend(values)
        else:
            lines.append("未定位到明显证据")
    return "\n".join(lines)


def main() -> None:
    client = SiliconFlowClient()
    if not client.is_enabled():
        raise RuntimeError("LLM_API_KEY 未配置")

    manifest = _load_manifest_records()
    for record in manifest:
        if record.get("status") != "downloaded":
            continue
        out_path = CACHE_DIR / f"{record['company_code']}_{record['year']}.json"
        if out_path.exists():
            try:
                existing = json.loads(out_path.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
            if (
                str(existing.get("source_url") or "") == str(record.get("source_url") or "")
                and str(existing.get("published_at") or "") == str(record.get("published_at") or "")
            ):
                print("skip", out_path.name)
                continue
            print("refresh", out_path.name)

        pdf_path = ROOT / str(record["local_path"])
        pages = read_pdf_pages(pdf_path)
        snippets = collect_snippets(pages)
        prompt = build_user_prompt(record, snippets)
        result = client.extract_json(SYSTEM_PROMPT, prompt)
        result["company_code"] = str(record["company_code"])
        result["report_year"] = int(record["year"])
        result["source_url"] = record["source_url"]
        result["published_at"] = record["published_at"]

        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        snippet_path = CACHE_DIR / f"{record['company_code']}_{record['year']}_snippets.json"
        snippet_path.write_text(json.dumps(snippets, ensure_ascii=False, indent=2), encoding="utf-8")
        print(out_path.name)


if __name__ == "__main__":
    main()


