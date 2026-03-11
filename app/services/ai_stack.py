from __future__ import annotations

from app.services.quality import DataQualityService
from app.services.risk_model import RiskModelService


class AIStackService:
    def __init__(self, risk_model_service: RiskModelService, quality_service: DataQualityService) -> None:
        self.risk_model_service = risk_model_service
        self.quality_service = quality_service

    def get_stack_summary(self) -> dict:
        risk_summary = self.risk_model_service.get_summary()
        quality_summary = self.quality_service.get_quality_summary()
        return {
            'engines': [
                {
                    'engine_id': 'agent-orchestrator',
                    'name': '任务型智能体编排引擎',
                    'category': 'NLP / LLM',
                    'status': 'active',
                    'role': '负责任务理解、对象锁定、任务模式切换、证据整合与结果生成。',
                    'primary_inputs': ['用户问题', '企业对象', '财报/研报/宏观证据'],
                    'primary_outputs': ['分析结论', '行动建议', '执行步骤', '阶段产物'],
                },
                {
                    'engine_id': 'risk-model',
                    'name': '风险预测模型',
                    'category': 'Tabular Deep Learning / ML',
                    'status': 'active' if risk_summary.get('model_ready') else 'warming_up',
                    'role': '对企业财务、趋势与经营特征进行风险评分与高风险概率预测。',
                    'primary_inputs': ['财务特征', '多年度趋势特征', '风险规则信号'],
                    'primary_outputs': ['风险等级', '高风险概率', '关键因子'],
                    'metrics': {
                        'sample_count': int(risk_summary.get('sample_count') or 0),
                        'roc_auc': risk_summary.get('metrics', {}).get('roc_auc'),
                        'model_type': risk_summary.get('model_type'),
                    },
                },
                {
                    'engine_id': 'multimodal-extractor',
                    'name': '多模态财报抽取引擎',
                    'category': 'CV / Vision-Language',
                    'status': 'active' if quality_summary.get('multimodal_extract_report_count', 0) else 'warming_up',
                    'role': '对复杂 PDF 财报中的图表、表格和版式进行视觉抽取并补成结构化证据。',
                    'primary_inputs': ['财报 PDF 页面图像', '表格与图表版面'],
                    'primary_outputs': ['结构化字段', '字段来源页面', '抽取说明'],
                    'metrics': {
                        'coverage_ratio': quality_summary.get('multimodal_extract_coverage_ratio'),
                        'avg_filled_field_count': quality_summary.get('multimodal_avg_filled_field_count'),
                        'backends': quality_summary.get('multimodal_backends', []),
                    },
                },
                {
                    'engine_id': 'data-governance',
                    'name': '数据治理与证据链引擎',
                    'category': 'Data Engineering',
                    'status': 'active',
                    'role': '负责多源异构数据接入、覆盖监控、异常检测、复核闭环与证据追溯。',
                    'primary_inputs': ['交易所财报', '研究报告', '宏观指标', '多模态抽取结果'],
                    'primary_outputs': ['质量摘要', '异常热区', '复核队列', '可信度状态'],
                    'metrics': {
                        'official_coverage_ratio': quality_summary.get('official_report_coverage_ratio'),
                        'pending_review_count': quality_summary.get('pending_review_count'),
                        'anomaly_company_count': quality_summary.get('anomaly_company_count'),
                    },
                },
            ],
            'design_choices': [
                '当前主链路以 NLP/LLM 编排为核心，不以 GNN 或知识图谱作为主引擎。',
                'CV/多模态主要服务于官方财报图表与表格抽取。',
                '风险预测采用表格特征模型，后续可继续升级为更强的深度学习版本。',
                '知识图谱与图学习可作为后续增强层，而不是当前主路径。',
            ],
        }
