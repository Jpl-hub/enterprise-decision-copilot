from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.vision_llm import VisionLLMClient

INVENTORY_PATH = ROOT / "data" / "raw" / "official" / "report_inventory.csv"
OUT_DIR = ROOT / "data" / "cache" / "official_extract_multimodal"
IMAGE_DIR = ROOT / "data" / "cache" / "official_page_images"

SYSTEM_PROMPT = """你是上市公司年报多模态抽取助手。你会接收年报页面图像和任务说明，只能基于图像中可见信息提取字段，禁止编造。

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
1. 金额统一输出为百万元数值，不带单位。
2. 百分比统一输出数值，不带 %。
3. 可推导字段允许基于同页可见公式推导，并在 notes 说明。
4. 若无法确认则填 null。
5. 不要输出 JSON 以外文本。
"""


class LocalQwenVLExtractor:
    def __init__(self, model_id: str) -> None:
        try:
            import torch
            from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
        except Exception as exc:
            raise RuntimeError("请先安装 transformers>=4.46，并确认环境支持 Qwen2.5-VL") from exc

        self.torch = torch
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
        )
        self.processor = AutoProcessor.from_pretrained(model_id)

    def _extract_json_text(self, output: str) -> str:
        text = str(output or "").strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
        return text

    def extract(self, user_prompt: str, image_paths: list[Path], max_new_tokens: int = 900) -> dict:
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": SYSTEM_PROMPT}],
            },
            {
                "role": "user",
                "content": [{"type": "image", "image": str(path)} for path in image_paths]
                + [{"type": "text", "text": user_prompt}],
            },
        ]

        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        try:
            from qwen_vl_utils import process_vision_info

            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            ).to(self.model.device)
        except Exception:
            inputs = self.processor(text=[text], images=image_paths, padding=True, return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        generated_ids_trimmed = [out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]
        return json.loads(self._extract_json_text(output_text))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="多模态抽取官方财报关键字段（API/ModelScope本地两种模式）")
    parser.add_argument("--backend", choices=["modelscope", "api"], default="modelscope", help="modelscope=本地模型推理，api=云端视觉API")
    parser.add_argument("--model-id", type=str, default="Qwen/Qwen2.5-VL-7B-Instruct", help="ModelScope/HF 模型 ID")
    parser.add_argument("--limit", type=int, default=6, help="最多处理多少个 company-year")
    parser.add_argument("--max-pages", type=int, default=6, help="每份报告最多渲染页数")
    parser.add_argument("--dpi", type=int, default=180, help="PDF 渲染 DPI")
    parser.add_argument("--sleep", type=float, default=0.8, help="每次请求后的 sleep 秒数")
    parser.add_argument("--max-new-tokens", type=int, default=900, help="仅 modelscope 模式生效")
    parser.add_argument("--force", action="store_true", help="覆盖已存在输出")
    return parser.parse_args()


def load_inventory() -> list[dict]:
    if not INVENTORY_PATH.exists():
        raise FileNotFoundError(f"未找到库存文件: {INVENTORY_PATH}")
    frame = pd.read_csv(INVENTORY_PATH, dtype={"company_code": str, "disclosure_company_code": str})
    if frame.empty:
        return []
    frame = frame[(frame["status"] == "downloaded") & (frame["file_exists"] == True)].copy()
    frame["year"] = frame["year"].astype(int)
    frame = frame.sort_values(["year", "published_at"], ascending=[False, False])
    return frame.to_dict("records")


def render_pdf_pages(pdf_path: Path, out_dir: Path, max_pages: int, dpi: int) -> list[Path]:
    try:
        import fitz  # type: ignore
    except Exception as exc:
        raise RuntimeError("缺少 PyMuPDF 依赖，请先安装 pymupdf>=1.24") from exc

    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    zoom = max(dpi / 72.0, 1.0)
    matrix = fitz.Matrix(zoom, zoom)
    image_paths: list[Path] = []
    for idx in range(min(max_pages, doc.page_count)):
        page = doc.load_page(idx)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        image_path = out_dir / f"page_{idx + 1:02d}.png"
        pix.save(image_path)
        image_paths.append(image_path)
    doc.close()
    return image_paths


def build_user_prompt(record: dict, image_paths: list[Path]) -> str:
    preview = "\n".join(f"- {path.name}" for path in image_paths)
    return "\n".join(
        [
            f"company_code: {record['company_code']}",
            f"report_year_target: {int(record['year'])}",
            f"source_url: {record.get('source_url') or ''}",
            "请根据附带页面图像抽取关键财务字段。",
            "页面文件：",
            preview,
        ]
    )


def main() -> None:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    api_client = None
    local_client = None
    if args.backend == "api":
        api_client = VisionLLMClient()
        if not api_client.is_enabled():
            raise RuntimeError("API 模式需要配置 VISION_LLM_API_KEY 或 LLM_API_KEY")
    else:
        local_client = LocalQwenVLExtractor(args.model_id)

    records = load_inventory()
    processed = 0
    for record in records:
        if processed >= args.limit:
            break

        company_code = str(record["company_code"])
        report_year = int(record["year"])
        output_path = OUT_DIR / f"{company_code}_{report_year}.json"
        if output_path.exists() and not args.force:
            print("skip", output_path.name)
            continue

        local_path = ROOT / str(record["local_path"])
        if not local_path.exists():
            print("missing_pdf", local_path)
            continue

        page_dir = IMAGE_DIR / f"{company_code}_{report_year}"
        image_paths = render_pdf_pages(local_path, page_dir, max_pages=args.max_pages, dpi=args.dpi)
        if not image_paths:
            print("empty_pages", local_path)
            continue

        prompt = build_user_prompt(record, image_paths)
        if args.backend == "api" and api_client is not None:
            result = api_client.extract_json_from_images(SYSTEM_PROMPT, prompt, image_paths=image_paths)
        elif local_client is not None:
            result = local_client.extract(prompt, image_paths=image_paths, max_new_tokens=args.max_new_tokens)
        else:
            raise RuntimeError("未初始化抽取后端")

        result["company_code"] = company_code
        result["report_year"] = report_year
        result["source_url"] = str(record.get("source_url") or "")
        result["published_at"] = str(record.get("published_at") or "")
        result["backend"] = args.backend
        result["model_id"] = args.model_id if args.backend == "modelscope" else "api"
        result["page_images"] = [str(path.relative_to(ROOT)) for path in image_paths]

        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("saved", output_path.name, "pages", len(image_paths), "backend", args.backend)
        processed += 1
        time.sleep(max(args.sleep, 0.0))

    print("done", {"processed": processed, "out_dir": str(OUT_DIR), "backend": args.backend})


if __name__ == "__main__":
    main()
