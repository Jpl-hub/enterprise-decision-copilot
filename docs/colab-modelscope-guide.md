# Colab + ModelScope 新手实操手册（A100 40GB）

## 0. 先统一项目主线（避免来回改方向）

本项目固定走这条主线：

1. 数据层：交易所财报 + 东方财富研报 + 宏观数据，做可追溯治理。
2. 模型层：多模态抽取（先推理，后 LoRA 微调）+ 风险预测（表格模型/时序模型）。
3. Agent 层：任务编排、证据引用、质量追踪。
4. 应用层：Web 展示 + 导出报告 + 答辩可视化。

说明：
- GNN / ViT / GraphRAG 不会因为“流行”直接入主线。
- 只有当它能显著提升可量化指标才进入核心路径。

## 1. VISION_LLM_API_KEY 是什么

它是云端视觉模型 API 的密钥。

- 你如果走 `ModelScope 本地推理`，可以先不需要它。
- 你如果走 `API 云端推理`，才需要它。

目前我们默认走本地：`--backend modelscope`。

## 2. Colab 一步一步操作

### Step A：挂载 Drive

```python
from google.colab import drive
drive.mount('/content/drive')
```

建议目录：`/content/drive/MyDrive/competition-2026/`

### Step B：准备代码与环境

```bash
%cd /content/drive/MyDrive/competition-2026
!git clone https://github.com/<你的仓库>.git my-agent
%cd my-agent

!pip install -U pip
!pip install -r requirements.txt
!pip install -U modelscope transformers accelerate bitsandbytes peft datasets qwen-vl-utils
```

### Step C：准备配置

```bash
!cp .env.example .env
```

本地 ModelScope 推理下，`.env` 里的 `VISION_LLM_API_KEY` 可以先留空。

### Step D：跑正式多模态主链路（不是 demo）

```bash
!python scripts/extract_official_financial_panel_multimodal.py \
  --backend modelscope \
  --model-id Qwen/Qwen2.5-VL-7B-Instruct \
  --limit 10 \
  --max-pages 6 \
  --dpi 180
```

### Step E：构建 SFT 数据集

```bash
!python scripts/build_multimodal_sft_dataset.py --min-fields 8 --out official_multimodal_sft.jsonl
```

输出：`data/datasets/official_multimodal_sft.jsonl`

## 3. A100 40GB 推荐策略

1. 推理阶段：先跑 7B 多模态模型，优先稳定和吞吐。
2. 训练阶段：LoRA + 4bit（QLoRA），先小样本验证，再全量训练。
3. 评测阶段：必须对比“微调前 vs 微调后”的字段级指标。

## 4. 固定工程规范（比赛+企业级）

1. 每次新增模型能力，必须附评测脚本与对比结果。
2. 每次新增功能，必须附测试与文档更新。
3. Agent 输出必须附证据路径与质量状态。

## 5. 智能体框架现状

当前是自研 Agent 主干（意图路由 + 工具注册 + 工作流追踪），不是黑盒框架。

优点：可解释、可测、可答辩。后续只做增强，不推翻主干。
