# 多模态与微调推进方案（比赛冲刺版）

## 1. 已落地代码

本轮已经新增两条可执行链路：

1. 多模态财报抽取脚本：`scripts/extract_official_financial_panel_multimodal.py`
2. 多模态 SFT 数据集构建脚本：`scripts/build_multimodal_sft_dataset.py`
3. 视觉大模型客户端：`app/services/vision_llm.py`

目标是把当前“纯文本抽取”升级为“页面图像 + 文本证据”的多模态抽取，并为后续 LoRA 微调准备训练数据。

## 2. 推荐平台分工

### Colab（你有教育优惠）

适合：

1. 小样本验证（20-200 条样本）
2. 跑多模态推理脚本验证提取质量
3. 跑轻量 LoRA 冒烟训练

### AutoDL

适合：

1. 批量推理（上千份年报页面）
2. 多轮 LoRA 训练（参数搜索）
3. 对比实验（Qwen-VL vs InternVL）

### HuggingFace / ModelScope

适合：

1. 拉取基座模型
2. 管理私有数据集与版本
3. 托管微调后的适配器权重

## 3. 建议模型路线

### 抽取模型（多模态）

优先顺序：

1. `Qwen2.5-VL`（中文财报场景友好）
2. `InternVL3`（多页文档理解能力强）

### 训练方式

1. 第一阶段：Prompt + few-shot，不训练
2. 第二阶段：LoRA（4bit/8bit）微调抽取格式稳定性
3. 第三阶段：加入 OCR 噪声样本进行鲁棒性强化

## 4. 你现在可直接执行

### Step A：生成多模态抽取结果

```bash
python scripts/extract_official_financial_panel_multimodal.py --limit 10 --max-pages 6 --dpi 180
```

### Step B：构建 SFT 数据集

```bash
python scripts/build_multimodal_sft_dataset.py --min-fields 8 --out official_multimodal_sft.jsonl
```

输出：`data/datasets/official_multimodal_sft.jsonl`

## 5. 你需要帮我准备的资源

请按优先级准备：

1. `VISION_LLM_API_KEY`（如果先走 API 多模态推理）
2. 一台可用 GPU 机器（建议 AutoDL 24G+ 显存）
3. 你倾向的模型源：HuggingFace 或 ModelScope（我会据此给你一键训练命令）
4. 是否允许我把训练产物目录统一为 `data/models/multimodal_lora/`

## 6. 比赛展示增益

这条线能显著提升三项评分：

1. 技术创新：从文本抽取升级到多模态文档理解
2. 工作量：数据构建、抽取、微调、评测全链路可证实
3. 完整度：抽取结果可追溯到具体页面图像与来源 URL
