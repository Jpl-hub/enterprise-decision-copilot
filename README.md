# 企航数策 Agent


当前版本按真实数据优先原则搭建：

- 数据来源限定为赛题给出的公开来源
- 不内置任何虚构财务或研报样本
- 先完成采集、清洗、分析、Agent、Web 展示的完整骨架
- 真实数据抓取完成后，系统即可直接驱动页面与问答
- 智能体链路采用“意图识别 + 工具注册 + 工作流编排 + 轨迹回显”的工程化模式

## 赛题对应关系

- 财报数据：上交所、深交所、北交所定期报告
- 研报数据：东方财富个股研报、行业研报
- 宏观数据：国家统计局国家数据平台
- AI 能力：基于真实数据的问答、对比、风险扫描、报告生成、决策简报

## 当前开发策略

第一阶段不追求“模型花哨”，而是先把获奖作品更关键的基础打牢：

- 真实数据采集链路
- 可解释的企业评分与风险预警
- 基于多年度财务趋势与语义检索的决策简报
- 证据可追溯的 Agent 工作流
- 可观测的工具执行轨迹
- 可演示的 Web 决策系统

## 当前架构

- 后端：FastAPI + Pydantic + Service Layer + Agent Workflow
- 前端：Vue 3 + TypeScript + Vite + Pinia + Vue Router
- 数据层：官方财报抓取、研报抓取、数据湖脚本、SQLite 本地应用库
- AI 层：Agent 编排、证据级 RAG、风险预测脚本

## 新增多模态能力（2026 冲刺）

- 多模态抽取脚本：`python scripts/extract_official_financial_panel_multimodal.py --limit 10`
- 多模态 SFT 数据集：`python scripts/build_multimodal_sft_dataset.py`
- 详细方案见：`docs/multimodal-roadmap.md`

## 启动方式

后端：

```bash
python -m uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://127.0.0.1:5173`，通过 Vite 代理访问后端 `http://127.0.0.1:8000`。

## 关于大模型

现阶段直接使用强模型 API 是可行的，但它只能解决“语言生成”问题，不能替代：

- 数据治理
- 行业指标体系
- 检索与归因
- 风险判定逻辑
- 结果验证与评测

微调不是第一优先级。只有当后续出现稳定、可量化、能被数据集支撑的性能瓶颈时，再考虑做轻量微调或偏好对齐。
