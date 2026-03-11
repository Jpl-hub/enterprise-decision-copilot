import shutil
import uuid
from pathlib import Path

from app.services.vision_llm import VisionLLMClient


def test_vision_llm_extract_json_text_from_fenced_block() -> None:
    client = VisionLLMClient(base_url="https://example.com", api_key="x", model="demo")
    text = "```json\n{\"a\":1,\"b\":2}\n```"
    assert client._extract_json_text(text) == '{"a":1,"b":2}'


def test_vision_llm_extract_json_text_from_plain_content() -> None:
    client = VisionLLMClient(base_url="https://example.com", api_key="x", model="demo")
    text = "结果如下：{\"ok\":true}"
    assert client._extract_json_text(text) == '{"ok":true}'


def test_vision_llm_encode_image_builds_data_uri() -> None:
    client = VisionLLMClient(base_url="https://example.com", api_key="x", model="demo")
    base = Path("data") / "test_temp" / uuid.uuid4().hex
    base.mkdir(parents=True, exist_ok=True)
    try:
        image = base / "x.png"
        image.write_bytes(b"fake")
        uri = client._encode_image(image)
        assert uri.startswith("data:image/png;base64,")
    finally:
        shutil.rmtree(base, ignore_errors=True)
