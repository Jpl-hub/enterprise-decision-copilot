# 企航数策 Agent

面向“智能体赋能的企业运营和决策分析系统”赛题的工程化原型。项目围绕真实公开数据构建企业分析、风险判断、证据检索、数据治理和智能体问答能力，强调可追溯、可演示、可扩展。

当前交接总文档见根目录 [需求和设计文档.md](./需求和设计文档.md)。

## 当前能力

- 企业分析工作台：围绕单一标的输出经营拆解、风险判断和证据锚点
- 企业对比：对多家公司做横向比较和结论归纳
- 智能体问答：按意图自动选择诊断、风险、对比、治理等分析路径
- 数据质量中心：展示覆盖率、复核、检索评估和治理状态
- 竞赛导出材料：生成适合演示与汇报的分析包

## 技术栈

- 后端：FastAPI、Pydantic、Service Layer、SQLite
- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router
- 检索：混合 TF-IDF 检索、关键词扩展、时效重排
- AI 工作流：意图路由、工具编排、证据归因、轨迹回显
- 数据脚本：多源公开数据处理、数据湖生成、评测脚本

## 目录结构

```text
app/         FastAPI 服务、智能体、业务服务
frontend/    Vue 前端
scripts/     数据处理、评测、启动脚本
data/        公开数据、评测样例、本地应用库
docs/        设计说明与专题文档
tests/       自动化测试
```

## 本地启动

### 1. 后端

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

默认地址：`http://127.0.0.1:8000`

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

默认地址：`http://127.0.0.1:5173`

如果前端和后端不在同一源上，前端可通过 `VITE_API_BASE` 指向后端地址。

## Docker 启动

根目录已提供 `Dockerfile`、`frontend/Dockerfile` 和 `docker-compose.yml`。

```bash
docker compose up --build
```

默认会启动：

- 后端 API
- 前端静态站点

## 环境变量

复制根目录 `.env.example` 为 `.env`，至少补齐模型相关密钥。

关键变量：

- `APP_NAME`：应用名称
- `TARGET_INDUSTRY`：默认目标行业
- `TARGET_POOL_MODE`：`core` 使用 6 家核心池，`expanded` 优先使用 `data/targets_expanded.csv`
- `TARGET_POOL_PATH`：自定义目标池 CSV 路径，优先级高于 `TARGET_POOL_MODE`
- `CORS_ORIGINS`：允许的前端来源，逗号分隔
- `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`
- `VISION_LLM_BASE_URL` / `VISION_LLM_API_KEY` / `VISION_LLM_MODEL`
- `AUTH_TOKEN_TTL_HOURS`：会话有效期
- `AUTH_COOKIE_NAME`：认证 Cookie 名称
- `AUTH_COOKIE_SECURE`：生产环境建议设为 `true`
- `AUTH_COOKIE_SAMESITE`：默认 `lax`
- `AUTH_COOKIE_DOMAIN`：按部署域名配置

## 认证与安全

- 当前 Web 端认证已切换为服务端 `HttpOnly` Cookie，会话不再写入前端 `localStorage`
- 仍保留后端 Bearer Token 解析能力，便于脚本或接口调试
- 生产环境建议：
  - 使用 HTTPS
  - 将 `AUTH_COOKIE_SECURE=true`
  - 收紧 `CORS_ORIGINS`
  - 定期清理历史会话和审计数据

## 测试与质量

后端测试：

```bash
pytest -q
```

前端构建验证：

```bash
cd frontend
npm run build
```

仓库已补充 GitHub Actions CI：

- 后端自动执行 `pytest -q`
- 前端自动执行 `npm run build`

## 目标池扩展

当前仓库默认核心演示池是 6 家医药生物企业，适合做稳定演示。为了支持比赛答辩和更强的横向比较，项目已补充“扩展目标池”能力。

基于当前仓库数据，已可生成一版 12 家扩展池：

- 核心 6 家：恒瑞医药、迈瑞医疗、爱尔眼科、益丰药房、联影医疗、药明康德
- 新增 6 家：爱美客、博雅生物、昆药集团、华润三九、天坛生物、凯莱英

生成命令：

```bash
python scripts/expand_target_pool.py --coverage-source financial --max-total 12 --min-feature-years 2
```

更严格的官方财报口径：

```bash
python scripts/expand_target_pool.py --coverage-source official --max-total 12 --min-feature-years 1
```

生成后可通过环境变量切换：

```bash
TARGET_POOL_MODE=expanded
```

输出文件：

- `data/targets_expanded.csv`
- `data/quality/targets_expanded_summary.json`

如果要把“候选生成 -> 候选年报抓取 -> 官方财报抽取 -> 双口径扩池”整条链一次跑完，可以使用：

```bash
python scripts/refresh_target_expansion_pipeline.py
```

该脚本会产出：

- `data/targets_expanded.csv`：扩展演示池
- `data/targets_expanded_strict.csv`：严格官方财报口径池
- `data/quality/target_pool_refresh_summary.json`：扩池刷新总览

## 数据说明

项目默认遵循“真实公开数据优先”原则，重点使用赛题允许的数据来源：

- 上交所、深交所、北交所公告与定期报告
- 东方财富个股/行业研报
- 国家统计局宏观数据

`data/source_registry.csv` 用于登记来源、用途和合规状态。新增来源前，建议先更新登记表。

## 当前边界

- 检索仍以词法/统计混合召回为主，尚未接入向量数据库
- 多模态和风险模型能力已具备脚手架，但仍有继续优化空间
- 部分数据脚本依赖人工准备公开原始数据

## 常用命令

```bash
pytest -q
python scripts/start_local_stack.ps1
python scripts/evaluate_retrieval_quality.py
python -m uvicorn app.main:app --reload
cd frontend && npm run build
```
