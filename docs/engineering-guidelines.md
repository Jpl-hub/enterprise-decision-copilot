# 工程规范对齐

## 目标

在不改变当前业务方向的前提下，将项目组织方式收敛到更接近企业级 FastAPI 与智能体工程的写法，重点解决：

- 入口文件过重
- 路由、Schema、服务耦合
- 后续多接口、多智能体、多模型扩展困难
- 系统演示和答辩时缺乏规范化叙事

## 当前采用的工程约束

### 1. 应用工厂

- 使用 `create_app()` 构建 FastAPI 应用
- 在生命周期中初始化数据库和服务容器
- 避免全局脚本式启动逻辑不断膨胀

### 2. 路由分层

- `app/api/routes/agent.py`
- `app/api/routes/dashboard.py`
- `app/api/routes/reports.py`
- `app/api/routes/briefs.py`
- `app/api/routes/health.py`
- `app/api/routes/web.py`

这样做的好处是：

- API 责任更清晰
- 便于版本化
- 后续可继续拆分智能体工具路由、管理员路由、数据任务路由

### 3. Schema 契约

- 所有核心请求/响应都通过 Pydantic Schema 约束
- 当前已补：
  - `app/schemas/agent.py`
  - `app/schemas/report.py`

这样后续接前后端联调、自动文档、测试都更稳。

### 4. 服务容器

- 通过 `app/core/container.py` 管理 `AnalyticsService`、`DecisionService` 与 `AgentService`
- 路由通过依赖注入访问服务
- 避免在每个文件里重复初始化服务对象

### 5. 表现层与业务层解耦

- 页面上下文构建抽到 `app/web/dashboard.py`
- 模板展示统一使用 `app/templates/` + `Jinja2Templates`
- 路由只负责接收请求、调用服务、返回响应
- 分析逻辑集中在 `AnalyticsService`
- 检索与决策逻辑拆到 `RetrievalService` / `DecisionService`
- 智能体编排逻辑集中在 `AgentService`

### 6. 智能体工具化编排

- 新增 `app/agents/` 模块，显式拆分：
  - `router.py` 负责意图识别
  - `tools.py` 负责可注册的分析工具
  - `workflow.py` 负责执行编排与轨迹记录
- `AgentService` 退化为薄服务，只负责调用工作流
- API 返回 `trace` 字段，前端可直接展示执行轨迹

这样做的价值是：

- 便于后续继续接入风险预测工具、RAG 检索工具、多模态年报理解工具
- 便于答辩时讲清“智能体不是聊天壳，而是会调工具的分析系统”
- 便于后续做工具级测试、性能监控、失败重试

## 与参考项目的对齐点

本次工程收敛时，重点参考了两类思路：

- 阿里云开发者文章中常见的企业 Web 工程拆分方式：应用工厂、分层路由、配置与生命周期管理
- AgentScope 这类智能体工程框架强调的模块化、可编排、可扩展思路

我们没有照搬其具体实现，而是吸收以下共性原则：

1. 业务能力必须模块化
2. 智能体调用链必须可扩展
3. 数据层、分析层、接口层要清晰分离
4. 系统需要可测试、可演示、可继续演进

## 下一阶段建议

后续系统继续深化时，工程上优先按这个方向扩展：

1. 增加 `report-generation`、`risk-forecast`、`retrieval` 子模块
2. 在现有 Tool 层上继续扩充可执行分析工具，而不是把逻辑塞回单个 Service
3. 把数据任务与在线服务进一步分离
4. 增加 API 契约测试和数据质量测试
