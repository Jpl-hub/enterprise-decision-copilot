from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.services.model_registry import ModelRegistryService
from app.services.quality import DataQualityService
from app.services.risk_model import RiskModelService
from app.services.vision_llm import VisionLLMClient


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / 'scripts'
COMPUTE_MANIFEST_PATH = ROOT / 'data' / 'quality' / 'compute_pipeline_manifest.json'


class AIStackService:
    def __init__(
        self,
        risk_model_service: RiskModelService,
        quality_service: DataQualityService,
        agent_skill_count: int = 9,
        model_registry_service: ModelRegistryService | None = None,
    ) -> None:
        self.risk_model_service = risk_model_service
        self.quality_service = quality_service
        self.agent_skill_count = agent_skill_count
        self.model_registry_service = model_registry_service or ModelRegistryService()

    def _safe_float(self, value: object, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _safe_int(self, value: object, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _clamp_score(self, value: float, cap: float = 0.96) -> float:
        return round(max(0.0, min(value, cap)), 2)

    def _status_from_score(self, score: float) -> str:
        if score >= 0.8:
            return 'active'
        if score >= 0.55:
            return 'building'
        return 'warming_up'

    def _readiness_label(self, score: float, active: str, building: str, warming: str) -> str:
        if score >= 0.8:
            return active
        if score >= 0.55:
            return building
        return warming

    def _line_count(self, path: Path) -> int:
        if not path.exists() or not path.is_file():
            return 0
        with path.open('r', encoding='utf-8') as fp:
            return sum(1 for line in fp if line.strip())

    def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return {}

    def _count_dataset_rows(self, dataset_dir: Path) -> tuple[int, int]:
        if not dataset_dir.exists():
            return 0, 0
        files = sorted(dataset_dir.glob('*.jsonl'))
        return len(files), sum(self._line_count(path) for path in files)

    def _count_matching_files(self, folder: Path, pattern: str) -> int:
        if not folder.exists():
            return 0
        return len(list(folder.glob(pattern)))

    def _headline_metric(self, label: str, value: str, tone: str = 'neutral') -> dict:
        return {'label': label, 'value': value, 'tone': tone}

    def _safe_path(self, path: Path) -> str | None:
        return str(path.resolve()) if path.exists() else None

    def _compute_manifest(self) -> dict:
        payload = self._read_json(COMPUTE_MANIFEST_PATH)
        if payload:
            return payload
        return {
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'current_engine': 'python + duckdb',
            'next_engine': 'spark-ready batch',
            'warehouse_db': None,
            'parquet_artifact_count': 0,
            'mart_views': [],
            'jobs': [],
        }

    def get_stack_summary(self) -> dict:
        risk_summary = self.risk_model_service.get_summary()
        quality_summary = self.quality_service.get_quality_summary()
        foundation_summary = self.quality_service.get_foundation_summary()
        compute_manifest = self._compute_manifest()

        model_dir = settings.cache_dir / 'models'
        multimodal_dir = settings.cache_dir / 'official_extract_multimodal'
        text_extract_dir = settings.cache_dir / 'official_extract'
        dataset_dir = settings.data_dir / 'datasets'

        model_artifact_count = len(list(model_dir.glob('*'))) if model_dir.exists() else 0
        dataset_file_count, dataset_sample_count = self._count_dataset_rows(dataset_dir)
        text_extract_report_count = self._count_matching_files(text_extract_dir, '*_snippets.json')
        multimodal_extract_count = self._count_matching_files(multimodal_dir, '*.json')

        risk_model_ready = bool(risk_summary.get('model_ready'))
        sequence_script_ready = (SCRIPT_DIR / 'train_risk_sequence_model.py').exists()
        sequence_model_ready = (model_dir / 'risk_lstm.keras').exists()
        multimodal_script_ready = (SCRIPT_DIR / 'extract_official_financial_panel_multimodal.py').exists()
        sft_script_ready = (SCRIPT_DIR / 'build_multimodal_sft_dataset.py').exists()
        vision_api_ready = VisionLLMClient().is_enabled()

        official_coverage_ratio = self._safe_float(quality_summary.get('official_report_coverage_ratio'))
        multimodal_coverage_ratio = self._safe_float(quality_summary.get('multimodal_extract_coverage_ratio'))
        pending_review_count = self._safe_int(quality_summary.get('pending_review_count'))

        warehouse_table_count = self._safe_int(foundation_summary.get('warehouse_table_count'))
        warehouse_row_count = self._safe_int(foundation_summary.get('total_warehouse_rows'))
        mart_view_count = len(foundation_summary.get('mart_views') or [])
        parquet_artifact_count = self._safe_int(foundation_summary.get('parquet_artifact_count'))
        official_inventory_rows = self._safe_int(foundation_summary.get('official_inventory_rows'))
        lake_layers = {str(item.get('layer') or '').lower() for item in foundation_summary.get('lake_layers') or []}
        gold_layer_ready = 'gold' in lake_layers
        spark_job_count = len(compute_manifest.get('jobs') or [])

        agent_score = self._clamp_score(
            0.35
            + min(official_coverage_ratio, 1.0) * 0.25
            + min(self.agent_skill_count / 9, 1.0) * 0.18
            + (0.12 if warehouse_row_count > 0 else 0.0)
            + (0.08 if pending_review_count <= 16 else 0.03)
            + 0.08,
            cap=0.93,
        )
        model_score = self._clamp_score(
            0.05
            + (0.18 if risk_model_ready else 0.0)
            + min(model_artifact_count / 4, 1.0) * 0.08
            + min(multimodal_coverage_ratio, 1.0) * 0.24
            + (0.07 if text_extract_report_count > 0 else 0.0)
            + (0.05 if sequence_script_ready else 0.0)
            + (0.18 if dataset_sample_count > 0 else 0.0)
            + (0.10 if sequence_model_ready else 0.0)
            + (0.05 if vision_api_ready else 0.0),
            cap=0.86,
        )
        data_score = self._clamp_score(
            0.18
            + (0.22 if foundation_summary.get('warehouse_db') else 0.0)
            + min(parquet_artifact_count / 15, 1.0) * 0.16
            + min(warehouse_table_count / 15, 1.0) * 0.14
            + min(warehouse_row_count / 10000, 1.0) * 0.18
            + min(mart_view_count / 6, 1.0) * 0.08
            + (0.08 if gold_layer_ready else 0.0)
            + (0.06 if official_inventory_rows > 0 else 0.0),
            cap=0.82,
        )
        multimodal_gap_text = (
            f'当前已完成 {multimodal_extract_count}/21 份多模态抽取，但复杂图表证据覆盖仍未达到稳定可用区间。'
            if multimodal_extract_count
            else '当前多模态抽取样本仍是 0，导致复杂图表证据还没有真正入链。'
        )
        multimodal_next_step = (
            f'继续把多模态抽取从 {multimodal_extract_count}/21 往全量推进，并把结果灌进企业分析证据流。'
            if multimodal_extract_count
            else '先批量跑一轮多模态财报抽取，把 0/21 提升到可展示区间。'
        )
        sft_gap_text = (
            f'当前已生成 {dataset_sample_count} 条样本，但离微调和评测所需的数据规模还差一个量级。'
            if dataset_sample_count
            else '目录当前为空，说明微调还没有真正进入数据准备阶段。'
        )
        deep_learning_stage = self._readiness_label(
            model_score,
            '表格模型上线，已形成首批多模态与 SFT 样本',
            '脚手架齐全，核心样本还没跑满',
            '只有脚本和设想，能力尚未真正接入',
        )

        pillars = [
            {
                'pillar_id': 'traditional-agent',
                'name': '传统应用 + Agent',
                'status': self._status_from_score(agent_score),
                'stage_label': self._readiness_label(agent_score, '面向用户的协同工作流已成形', '主链路可跑通，仍需持续打磨', '只完成底层能力，还没形成产品闭环'),
                'readiness_score': agent_score,
                'summary': '线程、任务模式、工作台、证据引用和执行轨迹已经串成主工作流，系统不再只是一个聊天框。',
                'headline_metrics': [
                    self._headline_metric('任务技能', f'{self.agent_skill_count} 个', 'positive'),
                    self._headline_metric('核心财报覆盖', f"{self._safe_int(quality_summary.get('official_report_downloaded_slots'))}/{self._safe_int(quality_summary.get('official_report_expected_slots'))}", 'positive'),
                    self._headline_metric('待处理问题', f'{pending_review_count} 项', 'warning' if pending_review_count else 'positive'),
                ],
                'strengths': [
                    'Agent 工作流具备意图识别、对象锁定、任务模式切换、plan/trace 回显。',
                    '首页、企业页、线程页已经形成可持续追问链路，不是单页静态展示。',
                    '分析结果能回连财报、研报、行业证据与数据质量状态。',
                ],
                'gaps': [
                    '企业页里的证据流和任务轨迹还可以再做得更强，不够竞赛级震撼。',
                    '多角色协同和批处理任务调度还没有进系统主界面。',
                ],
                'next_steps': [
                    '把工作台里的任务执行轨迹、证据引用和导出动作做成一条完整操作链。',
                    '把重点任务卡和批处理任务连接到更多真实服务，而不是只停留在单企业交互。',
                ],
            },
            {
                'pillar_id': 'deep-learning',
                'name': '深度学习 / 大模型',
                'status': self._status_from_score(model_score),
                'stage_label': deep_learning_stage,
                'readiness_score': model_score,
                'summary': '风险表格模型已经有真实产物，但多模态财报抽取、SFT 数据集和序列模型仍处于待启动或实验态。',
                'headline_metrics': [
                    self._headline_metric('风险模型产物', f'{model_artifact_count} 个', 'positive' if risk_model_ready else 'warning'),
                    self._headline_metric('多模态抽取', f'{multimodal_extract_count}/{self._safe_int(quality_summary.get("multimodal_expected_report_count"))}', 'warning'),
                    self._headline_metric('SFT 样本', f'{dataset_sample_count} 条', 'warning' if dataset_sample_count == 0 else 'positive'),
                ],
                'strengths': [
                    '已经具备风险表格模型、视觉大模型客户端、多模态抽取脚本、SFT 数据集构建脚本。',
                    '仓内已有文本抽取缓存，可作为多模态训练前的辅助证据层。',
                    'README 和路线文档已经把 Qwen2.5-VL / LoRA / ModelScope 方向写进工程路线。',
                ],
                'gaps': [
                    multimodal_gap_text,
                    sft_gap_text,
                    'LSTM 序列脚本已在仓内，但没有保存好的模型产物和评测结果。',
                ],
                'next_steps': [
                    multimodal_next_step,
                    (
                        f'继续扩充 SFT 样本，从当前 {dataset_sample_count} 条往可微调规模推进，并对接 ModelScope / ms-swift。'
                        if dataset_sample_count
                        else '生成第一版 SFT 数据集，后续对接 ModelScope / ms-swift 做轻量微调实验。'
                    ),
                    '把序列风险模型训练结果纳入统一模型管理，而不是只留训练脚本。',
                ],
            },
            {
                'pillar_id': 'big-data',
                'name': '大数据 / 计算引擎',
                'status': self._status_from_score(data_score),
                'stage_label': self._readiness_label(data_score, '单机湖仓与主题 mart 已成形', '湖仓结构已搭好，计算规模仍需放大', '只有零散文件，还没有形成统一计算底座'),
                'readiness_score': data_score,
                'summary': '真实数据已经沉到 Bronze / Silver / Gold 和 DuckDB mart，但当前仍属于单机湖仓阶段，分布式计算引擎还没引入。',
                'headline_metrics': [
                    self._headline_metric('仓表视图', f'{warehouse_table_count} 张', 'positive'),
                    self._headline_metric('Spark-ready 作业', f'{spark_job_count} 个', 'positive' if spark_job_count else 'warning'),
                    self._headline_metric('总行数', f'{warehouse_row_count:,}', 'positive'),
                ],
                'strengths': [
                    'Bronze / Silver / Gold 分层、Parquet 落盘、DuckDB mart 和质量报告已经全部跑通。',
                    '研报、行业、宏观、官方财报清单都已进入统一仓层，后续可继续扩容。',
                    '质量页已经能直接看到数据规模、空值热点、主题数据集和定期披露覆盖。',
                ],
                'gaps': [
                    '当前还是单机湖仓，Spark/Flink 这类分布式计算引擎尚未接入。',
                    '数据规模已经可演示，但距离比赛级“大样本、高吞吐”还要再扩一层。',
                ],
                'next_steps': [
                    '给现有湖仓补一层 Spark-ready 的批处理接口和任务说明，明确可扩展方向。',
                    '继续扩充企业池和官方报告样本，把仓层规模从演示级拉到竞赛级。',
                ],
            },
        ]

        engines = [
            {
                'engine_id': 'agent-orchestrator',
                'name': '任务型智能体编排引擎',
                'category': 'Traditional App + Agent',
                'status': self._status_from_score(agent_score),
                'stage_label': '线程化工作流',
                'readiness_score': agent_score,
                'role': '负责任务理解、对象锁定、技能路由、证据整合、结果生成与线程上下文承接。',
                'primary_inputs': ['用户问题', '企业对象', '财报/研报/宏观证据'],
                'primary_outputs': ['分析结论', '行动建议', 'plan / trace', '线程记忆'],
                'headline_metrics': [
                    self._headline_metric('技能', f'{self.agent_skill_count} 个'),
                    self._headline_metric('轨迹', 'plan + trace'),
                    self._headline_metric('主样本覆盖', f'{official_coverage_ratio * 100:.1f}%'),
                ],
                'gaps': ['还缺跨企业批处理与更强的证据流呈现。'],
                'metrics': {
                    'tool_count': self.agent_skill_count,
                    'official_coverage_ratio': official_coverage_ratio,
                    'pending_review_count': pending_review_count,
                    'anomaly_company_count': self._safe_int(quality_summary.get('anomaly_company_count')),
                },
            },
            {
                'engine_id': 'risk-model',
                'name': '风险预测模型',
                'category': 'Deep Learning / ML',
                'status': 'active' if risk_model_ready else 'warming_up',
                'stage_label': '表格模型已落盘' if risk_model_ready else '待训练',
                'readiness_score': 0.72 if risk_model_ready else 0.22,
                'role': '对企业财务、趋势与经营特征进行风险评分与高风险概率预测。',
                'primary_inputs': ['财务特征', '多年度趋势特征', '风险规则信号'],
                'primary_outputs': ['风险等级', '高风险概率', '关键因子'],
                'headline_metrics': [
                    self._headline_metric('样本', f"{self._safe_int(risk_summary.get('sample_count'))} 条"),
                    self._headline_metric('ROC-AUC', f"{self._safe_float((risk_summary.get('metrics') or {}).get('roc_auc')):.3f}"),
                    self._headline_metric('特征', f"{len(risk_summary.get('feature_columns') or [])} 个"),
                ],
                'gaps': ['样本量仍偏小，指标还不足以支撑更强的比赛口径。'],
                'metrics': {
                    'sample_count': self._safe_int(risk_summary.get('sample_count')),
                    'roc_auc': self._safe_float((risk_summary.get('metrics') or {}).get('roc_auc')),
                    'model_type': risk_summary.get('model_type'),
                    'trained_at': risk_summary.get('trained_at'),
                    'feature_count': len(risk_summary.get('feature_columns') or []),
                    'artifact_count': model_artifact_count,
                },
            },
            {
                'engine_id': 'sequence-risk-lab',
                'name': '时序风险实验引擎',
                'category': 'Deep Learning',
                'status': 'active' if sequence_model_ready else ('building' if sequence_script_ready else 'warming_up'),
                'stage_label': '序列模型已产出' if sequence_model_ready else ('序列训练脚本已就绪' if sequence_script_ready else '未接入'),
                'readiness_score': 0.68 if sequence_model_ready else (0.39 if sequence_script_ready else 0.18),
                'role': '面向连续多年财务序列的风险时序建模，为后续深度学习增强留出接口。',
                'primary_inputs': ['多年度财务序列', '风险标签'],
                'primary_outputs': ['LSTM 模型产物', '验证 AUC'],
                'headline_metrics': [
                    self._headline_metric('训练脚本', '已存在' if sequence_script_ready else '缺失', 'positive' if sequence_script_ready else 'warning'),
                    self._headline_metric('模型产物', '已保存' if sequence_model_ready else '未生成', 'positive' if sequence_model_ready else 'warning'),
                    self._headline_metric('序列长度', '3 年窗口'),
                ],
                'gaps': ['当前还没有统一纳入模型管理与页面呈现。'],
                'metrics': {
                    'artifact_count': 1 if sequence_model_ready else 0,
                },
            },
            {
                'engine_id': 'multimodal-extractor',
                'name': '多模态财报抽取引擎',
                'category': 'Vision-Language',
                'status': 'active' if multimodal_extract_count else ('building' if multimodal_script_ready else 'warming_up'),
                'stage_label': '抽取结果已入链' if multimodal_extract_count else ('抽取脚本已就绪' if multimodal_script_ready else '未接入'),
                'readiness_score': self._clamp_score(0.18 + min(multimodal_coverage_ratio, 1.0) * 0.55 + (0.12 if vision_api_ready else 0.0), cap=0.79),
                'role': '对复杂 PDF 财报中的表格、图表和版式做视觉抽取，补齐文本抽取无法稳定覆盖的字段。',
                'primary_inputs': ['财报 PDF 页面图像', '图表/表格版面'],
                'primary_outputs': ['结构化字段', '字段来源页面', '抽取说明'],
                'headline_metrics': [
                    self._headline_metric('抽取覆盖', f'{multimodal_extract_count}/{self._safe_int(quality_summary.get("multimodal_expected_report_count"))}'),
                    self._headline_metric('文本缓存', f'{text_extract_report_count} 份'),
                    self._headline_metric('视觉 API', '已配置' if vision_api_ready else '未配置', 'positive' if vision_api_ready else 'warning'),
                ],
                'gaps': [multimodal_gap_text],
                'metrics': {
                    'coverage_ratio': multimodal_coverage_ratio,
                    'avg_filled_field_count': self._safe_float(quality_summary.get('multimodal_avg_filled_field_count')),
                    'backends': list(quality_summary.get('multimodal_backends') or []),
                    'extract_report_count': multimodal_extract_count,
                    'expected_report_count': self._safe_int(quality_summary.get('multimodal_expected_report_count')),
                    'text_extract_report_count': text_extract_report_count,
                },
            },
            {
                'engine_id': 'sft-dataset-factory',
                'name': '多模态 SFT 数据集工厂',
                'category': 'Fine-tuning',
                'status': 'active' if dataset_sample_count else ('building' if sft_script_ready else 'warming_up'),
                'stage_label': '可直接训练' if dataset_sample_count else ('脚本已就绪' if sft_script_ready else '未接入'),
                'readiness_score': 0.73 if dataset_sample_count else (0.31 if sft_script_ready else 0.14),
                'role': '把页面图像、多模态抽取结果和官方标签整理成后续微调使用的标准样本。',
                'primary_inputs': ['页面图像', '文本证据缓存', '官方标签'],
                'primary_outputs': ['JSONL SFT 样本', '训练标签映射'],
                'headline_metrics': [
                    self._headline_metric('数据集文件', f'{dataset_file_count} 个'),
                    self._headline_metric('训练样本', f'{dataset_sample_count} 条'),
                    self._headline_metric('路线', 'ModelScope / LoRA'),
                ],
                'gaps': [sft_gap_text],
                'metrics': {
                    'sft_sample_count': dataset_sample_count,
                    'artifact_count': dataset_file_count,
                },
            },
            {
                'engine_id': 'data-governance',
                'name': '数据治理与证据链引擎',
                'category': 'Data Engineering',
                'status': 'active',
                'stage_label': '真实数据治理运行中',
                'readiness_score': self._clamp_score(0.42 + official_coverage_ratio * 0.18 + (0.12 if official_inventory_rows > 0 else 0.0), cap=0.88),
                'role': '负责多源异构数据接入、覆盖监控、异常检测、问题排队与证据追溯。',
                'primary_inputs': ['交易所财报', '研究报告', '宏观指标', '多模态结果'],
                'primary_outputs': ['质量摘要', '异常热区', '待处理问题', '可信度判断'],
                'headline_metrics': [
                    self._headline_metric('异常企业', f"{self._safe_int(quality_summary.get('anomaly_company_count'))} 家"),
                    self._headline_metric('待处理问题', f'{pending_review_count} 项'),
                    self._headline_metric('官方清单', f'{official_inventory_rows} 份'),
                ],
                'gaps': ['多模态字段补全还没有覆盖到治理闭环。'],
                'metrics': {
                    'official_coverage_ratio': official_coverage_ratio,
                    'pending_review_count': pending_review_count,
                    'anomaly_company_count': self._safe_int(quality_summary.get('anomaly_company_count')),
                },
            },
            {
                'engine_id': 'lakehouse-compute',
                'name': '湖仓与主题计算引擎',
                'category': 'Big Data',
                'status': self._status_from_score(data_score),
                'stage_label': 'Bronze / Silver / Gold 已成形',
                'readiness_score': data_score,
                'role': '负责 Parquet 数据湖、DuckDB 分析仓、主题 mart 和质量画像，为后续大规模计算扩展打底。',
                'primary_inputs': ['Bronze / Silver / Gold 数据层', 'Parquet 产物'],
                'primary_outputs': ['DuckDB mart', '仓层统计', '主题视图'],
                'headline_metrics': [
                    self._headline_metric('仓表视图', f'{warehouse_table_count} 张'),
                    self._headline_metric('主题 mart', f'{mart_view_count} 个'),
                    self._headline_metric('Spark-ready 作业', f'{spark_job_count} 个'),
                ],
                'gaps': ['分布式计算引擎仍未进入主链路，当前是单机湖仓。'],
                'metrics': {
                    'warehouse_table_count': warehouse_table_count,
                    'warehouse_row_count': warehouse_row_count,
                    'mart_view_count': mart_view_count,
                    'parquet_artifact_count': parquet_artifact_count,
                },
            },
        ]

        return {
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'pillars': pillars,
            'engines': engines,
            'priority_actions': [
                '优先补跑多模态财报抽取，把复杂图表证据真正送进企业分析链路。',
                '生成第一批 SFT 样本并接入 ModelScope / ms-swift 微调试验，形成深度学习闭环。',
                '给现有 Parquet + DuckDB 湖仓补上 Spark-ready 批处理接口，明确大数据赛道扩展路线。',
                '继续扩充目标企业和官方报告样本，把风险模型和序列模型的训练样本抬上去。',
            ],
            'system_story': [
                '传统应用层不再把问答孤立成聊天窗，而是用线程、工作台和任务流承接真实协作。',
                'AI 层先用表格风险模型、多模态抽取和证据级检索落地，再逐步扩到微调与序列建模。',
                '数据层先以单机湖仓跑通真实链路，再把分布式计算引擎作为第二阶段增强，而不是一开始空谈大数据。',
            ],
            'design_choices': [
                '当前主链路以真实数据 + Agent 编排为核心，不把知识图谱或复杂多代理作为第一优先。',
                '深度学习层优先服务于风险预测与财报多模态解析，而不是泛化成无落点的大模型演示。',
                '大数据层先保证数据真实、可追溯、可量化，再逐步扩到更大规模计算与训练资源。',
            ],
        }

    def get_engine_room_summary(self) -> dict:
        quality_summary = self.quality_service.get_quality_summary()
        compute_manifest = self._compute_manifest()
        registry_summary = self.model_registry_service.get_summary()

        dataset_dir = settings.data_dir / 'datasets'
        sft_dataset_path = dataset_dir / 'official_multimodal_sft.jsonl'

        dataset_file_count, dataset_sample_count = self._count_dataset_rows(dataset_dir)
        multimodal_expected_count = self._safe_int(quality_summary.get('multimodal_expected_report_count'))
        jobs = [dict(item) for item in list(compute_manifest.get('jobs') or []) if isinstance(item, dict)]
        spark_ready_job_count = sum(1 for item in jobs if bool(item.get('spark_ready')))
        model_registry = [dict(item) for item in registry_summary.get('items') or []]

        recommended_actions = [
            f'当前 Spark-ready 计算任务 {spark_ready_job_count}/{len(jobs)} 个，下一步应把批处理作业接入调度而不只是脚本清单。',
            (
                f"多模态抽取已覆盖 {next((item.get('sample_count') for item in model_registry if item.get('model_id') == 'multimodal-extractor'), 0)}/{multimodal_expected_count} 份财报，继续补齐后才能稳定支撑复杂图表问答。"
                if multimodal_expected_count
                else '多模态抽取目标规模尚未入表，需要先明确 expected_report_count。'
            ),
            (
                f'当前 SFT 样本 {dataset_sample_count} 条，仍需继续扩样后再做轻量微调验证。'
                if dataset_sample_count
                else '当前 SFT 数据集还为空，应优先产出首版训练样本。'
            ),
        ]
        recommended_actions.extend(list(registry_summary.get('priority_actions') or [])[:2])

        return {
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'compute_pipeline': {
                'current_engine': str(compute_manifest.get('current_engine') or 'python + duckdb'),
                'next_engine': str(compute_manifest.get('next_engine') or 'spark-ready batch'),
                'warehouse_db': str(compute_manifest.get('warehouse_db') or '') or None,
                'job_count': len(jobs),
                'spark_ready_job_count': spark_ready_job_count,
                'parquet_artifact_count': self._safe_int(compute_manifest.get('parquet_artifact_count')),
                'mart_views': [str(item) for item in list(compute_manifest.get('mart_views') or []) if str(item)],
                'jobs': jobs,
            },
            'model_registry': model_registry,
            'recommended_actions': recommended_actions,
        }
