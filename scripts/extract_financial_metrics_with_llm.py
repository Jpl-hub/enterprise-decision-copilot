from __future__ import annotations

import sys
from pathlib import Path

from PyPDF2 import PdfReader

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
from app.services.llm import SiliconFlowClient


SYSTEM_PROMPT = """你是财报结构化抽取助手。请从用户提供的上市公司定期报告文本中提取关键经营指标，并严格输出 JSON。字段包括：company_name, report_year, revenue_million, net_profit_million, gross_margin_pct, net_margin_pct, rd_ratio_pct, debt_ratio_pct, current_ratio, cash_to_short_debt, inventory_turnover, receivable_turnover, operating_cashflow_million, roe_pct。若无法确定则填 null，不要编造。"""


def read_pdf_text(path: Path, max_pages: int = 20) -> str:
    reader = PdfReader(str(path))
    chunks = []
    for page in reader.pages[:max_pages]:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


def main() -> None:
    pdf_dir = settings.raw_dir / "pdfs"
    pdf_paths = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_paths:
        print("未找到待抽取的 PDF，请先下载真实财报到 data/raw/pdfs/")
        return

    client = SiliconFlowClient()
    if not client.is_enabled():
        print("未配置 LLM_API_KEY，暂无法执行基于模型的财报指标抽取。")
        return

    for path in pdf_paths:
        text = read_pdf_text(path)
        user_prompt = f"文件名：{path.name}\n请基于以下文本提取关键经营指标：\n{text[:30000]}"
        result = client.extract_json(SYSTEM_PROMPT, user_prompt)
        output = settings.cache_dir / f"{path.stem}.json"
        output.write_text(__import__('json').dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已输出：{output}")


if __name__ == "__main__":
    main()
