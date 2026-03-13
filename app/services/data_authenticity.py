from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from app.config import settings


class DataAuthenticityService:
    def __init__(self, source_registry_path: Path | None = None) -> None:
        self.source_registry_path = source_registry_path
        self.allowed_domains = self._load_allowed_domains()

    def _registry_candidates(self) -> list[Path]:
        explicit = [self.source_registry_path] if self.source_registry_path else []
        return [
            *(path for path in explicit if path is not None),
            settings.data_dir / 'source_registry.csv',
            settings.processed_dir / 'source_registry.csv',
            settings.data_dir / 'lake' / 'silver' / 'source_registry' / 'part-0000.csv',
            settings.data_dir / 'lake' / 'bronze' / 'source_registry' / 'part-0000.csv',
        ]

    def _read_registry(self) -> pd.DataFrame:
        for path in self._registry_candidates():
            if path.exists():
                return pd.read_csv(path)
        return pd.DataFrame()

    def _extract_domain(self, value: object) -> str | None:
        text = str(value or '').strip()
        if not text or text.startswith('/'):
            return None
        if '://' not in text:
            if '/' not in text and '.' in text:
                return text.lower()
            return None
        host = str(urlparse(text).netloc or '').strip().lower()
        return host or None

    def _domain_family_aliases(self, domain: str) -> set[str]:
        normalized = domain.lower().strip()
        aliases = {normalized}
        if normalized.endswith('sse.com.cn'):
            aliases.update({'www.sse.com.cn', 'query.sse.com.cn', 'static.sse.com.cn'})
        if normalized.endswith('szse.cn'):
            aliases.update({'www.szse.cn', 'disc.static.szse.cn'})
        if normalized.endswith('bse.cn'):
            aliases.update({'www.bse.cn'})
        if normalized.endswith('eastmoney.com'):
            aliases.update({'data.eastmoney.com', 'reportapi.eastmoney.com', 'datacenter-web.eastmoney.com'})
        if normalized.endswith('stats.gov.cn'):
            aliases.update({'www.stats.gov.cn', 'stats.gov.cn'})
        return aliases

    def _load_allowed_domains(self) -> set[str]:
        registry = self._read_registry()
        allowed: set[str] = set()
        if registry.empty or 'domain' not in registry.columns:
            return allowed
        for value in registry['domain'].dropna().tolist():
            domain = self._extract_domain(value)
            if not domain:
                continue
            allowed.update(self._domain_family_aliases(domain))
        return allowed

    def _infer_source_type(self, domain: str) -> str:
        if domain.endswith('sse.com.cn') or domain.endswith('szse.cn') or domain.endswith('bse.cn'):
            return 'financial'
        if domain.endswith('eastmoney.com'):
            return 'research'
        if domain.endswith('stats.gov.cn'):
            return 'macro'
        return 'unknown'

    def collect_urls(self, payload: object) -> list[str]:
        urls: list[str] = []

        def _walk(value: object) -> None:
            if isinstance(value, dict):
                for nested in value.values():
                    _walk(nested)
                return
            if isinstance(value, list):
                for nested in value:
                    _walk(nested)
                return
            text = str(value or '').strip()
            if text.startswith('http://') or text.startswith('https://'):
                urls.append(text)

        _walk(payload)
        return list(dict.fromkeys(urls))

    def summarize_urls(
        self,
        urls: list[str],
        *,
        required_source_types: list[str] | None = None,
        scope_label: str = '分析结果',
    ) -> dict:
        required = [str(item).strip() for item in list(required_source_types or []) if str(item).strip()]
        domains = sorted({self._extract_domain(url) for url in urls if self._extract_domain(url)})
        approved_domains = [domain for domain in domains if domain in self.allowed_domains]
        unapproved_domains = [domain for domain in domains if domain not in self.allowed_domains]
        source_types_present = sorted(
            {
                source_type
                for source_type in (self._infer_source_type(domain) for domain in approved_domains)
                if source_type != 'unknown'
            }
        )
        missing_source_types = [item for item in required if item not in source_types_present]
        approved_source_only = len(domains) > 0 and not unapproved_domains
        verifiable = len(domains) > 0
        real_data_only = approved_source_only and not missing_source_types
        if unapproved_domains:
            trust_status = 'blocked'
        elif real_data_only:
            trust_status = 'trusted'
        elif verifiable:
            trust_status = 'watch'
        else:
            trust_status = 'limited'

        warnings: list[str] = []
        if not verifiable:
            warnings.append(f'{scope_label}当前没有可核验的外部来源 URL。')
        if unapproved_domains:
            warnings.append(f"{scope_label}存在未登记域名：{', '.join(unapproved_domains[:4])}。")
        if missing_source_types:
            warnings.append(f"{scope_label}缺少所需来源类型：{', '.join(missing_source_types)}。")

        if real_data_only:
            statement = f'{scope_label}当前仅使用赛题允许来源，可回链核验。'
        elif approved_source_only and verifiable:
            statement = f'{scope_label}来源均已登记，但部分必要来源尚未覆盖完全。'
        elif verifiable:
            statement = f'{scope_label}存在来源合规风险，当前不应视为企业级正式输出。'
        else:
            statement = f'{scope_label}当前缺少可核验来源，只能视为未完成结果。'

        return {
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'real_data_only': real_data_only,
            'approved_source_only': approved_source_only,
            'verifiable': verifiable,
            'trust_status': trust_status,
            'evidence_url_count': len(urls),
            'observed_domains': domains,
            'approved_domains': approved_domains,
            'unapproved_domains': unapproved_domains,
            'source_types_present': source_types_present,
            'required_source_types': required,
            'missing_source_types': missing_source_types,
            'statement': statement,
            'warnings': warnings,
        }

    def summarize_evidence(
        self,
        evidence: object,
        *,
        required_source_types: list[str] | None = None,
        scope_label: str = '分析结果',
    ) -> dict:
        return self.summarize_urls(
            self.collect_urls(evidence),
            required_source_types=required_source_types,
            scope_label=scope_label,
        )

    def summarize_frames(
        self,
        *,
        financials: pd.DataFrame,
        research_reports: pd.DataFrame,
        industry_reports: pd.DataFrame,
        macro: pd.DataFrame,
        scope_label: str = '系统数据底座',
    ) -> dict:
        urls: list[str] = []
        for frame, column in (
            (financials, 'source_url'),
            (research_reports, 'source_url'),
            (industry_reports, 'source_url'),
            (macro, 'source_url'),
        ):
            if frame.empty or column not in frame.columns:
                continue
            urls.extend(str(item).strip() for item in frame[column].dropna().tolist() if str(item).strip())
        payload = self.summarize_urls(
            list(dict.fromkeys(urls)),
            required_source_types=['financial', 'research', 'macro'],
            scope_label=scope_label,
        )
        payload['record_counts'] = {
            'financial_rows': int(len(financials)),
            'research_rows': int(len(research_reports)),
            'industry_report_rows': int(len(industry_reports)),
            'macro_rows': int(len(macro)),
        }
        return payload

    def infer_required_source_types(self, evidence: dict | None) -> list[str]:
        payload = dict(evidence or {})
        required: list[str] = []
        if payload.get('financial_source_url') or payload.get('companies'):
            required.append('financial')
        if payload.get('research_reports') or payload.get('industry_reports') or payload.get('semantic_stock_reports') or payload.get('semantic_industry_reports'):
            required.append('research')
        if payload.get('macro_items'):
            required.append('macro')
        return list(dict.fromkeys(required))
