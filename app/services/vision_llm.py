from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any

import httpx

from app.config import settings


class VisionLLMClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.vision_llm_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else (settings.vision_llm_api_key or settings.llm_api_key)
        self.model = model or settings.vision_llm_model

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    def _extract_json_text(self, content: str) -> str:
        text = str(content or "").strip()
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
        if fenced:
            return fenced.group(1)
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
        return text

    def _encode_image(self, image_path: Path) -> str:
        media_type = "image/png"
        suffix = image_path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            media_type = "image/jpeg"
        payload = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        return f"data:{media_type};base64,{payload}"

    def chat_with_images(
        self,
        system_prompt: str,
        user_prompt: str,
        image_paths: list[Path],
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        if not self.is_enabled():
            raise RuntimeError("VISION_LLM_API_KEY 或 LLM_API_KEY 未配置")

        content: list[dict[str, Any]] = [{"type": "text", "text": user_prompt}]
        for image_path in image_paths:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self._encode_image(image_path)},
                }
            )

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
            },
            timeout=240,
        )
        response.raise_for_status()
        return response.json()

    def extract_json_from_images(
        self,
        system_prompt: str,
        user_prompt: str,
        image_paths: list[Path],
    ) -> dict[str, Any]:
        payload = self.chat_with_images(system_prompt, user_prompt, image_paths)
        content = payload["choices"][0]["message"]["content"]
        json_text = self._extract_json_text(content)
        return json.loads(json_text)
