from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config import settings


class SiliconFlowClient:
    def __init__(self) -> None:
        self.base_url = settings.llm_base_url.rstrip("/")
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict[str, Any]:
        if not self.is_enabled():
            raise RuntimeError("LLM API key 未配置")
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
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()

    def _extract_json_text(self, content: str) -> str:
        content = content.strip()
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.S)
        if fenced:
            return fenced.group(1)
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return content[start:end + 1]
        return content

    def extract_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        payload = self.chat(system_prompt, user_prompt)
        content = payload["choices"][0]["message"]["content"]
        json_text = self._extract_json_text(content)
        return json.loads(json_text)
