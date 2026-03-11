from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings


for path in [settings.raw_dir, settings.processed_dir, settings.cache_dir]:
    path.mkdir(parents=True, exist_ok=True)

for sub in [
    settings.raw_dir / "announcements",
    settings.raw_dir / "reports",
    settings.raw_dir / "macro",
    settings.raw_dir / "pdfs",
]:
    sub.mkdir(parents=True, exist_ok=True)

print("已初始化真实数据目录：")
for path in [settings.raw_dir, settings.processed_dir, settings.cache_dir]:
    print(path)
