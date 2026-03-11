# 真实数据接入说明

## 官方来源

1. 上交所定期报告：https://www.sse.com.cn/disclosure/listedinfo/regular/
2. 深交所定期报告：https://www.szse.cn/disclosure/listed/fixed/index.html
3. 北交所公告页：https://www.bse.cn/disclosure/announcement.html
4. 东方财富个股研报：https://data.eastmoney.com/report/stock.jshtml
5. 东方财富行业研报：https://data.eastmoney.com/report/industry.jshtml
6. 国家统计局国家数据：https://www.stats.gov.cn/sj/

## 当前仓库中的脚本

- `python scripts/prepare_data_dirs.py`
  初始化 `data/raw/`、`data/processed/`、`data/cache/`

- `python scripts/build_announcement_tasks.py`
  生成目标企业公告抓取任务清单

- `python scripts/init_processed_templates.py`
  初始化财报结构化结果模板

- `python scripts/init_report_template.py`
  初始化研报结构化文件

- `python scripts/init_macro_template.py`
  初始化宏观指标文件

- `python scripts/extract_financial_metrics_with_llm.py`
  将下载好的真实财报 PDF 文本交给模型做结构化抽取

## 推荐执行顺序

1. 运行目录初始化脚本。
2. 访问交易所页面，按目标企业下载最近 3-4 年定期报告 PDF 到 `data/raw/pdfs/`。
3. 运行财报指标抽取脚本，生成缓存 JSON。
4. 人工复核关键指标后写入 `data/processed/financial_features.csv`。
5. 抓取东方财富研报列表与摘要，写入 `data/processed/research_reports.csv`。
6. 从国家统计局整理宏观指标，写入 `data/processed/macro_indicators.csv`。
7. 重启 Web 服务，系统自动切换到真实分析模式。

## 当前阻塞点

当前工作环境的命令行网络访问被限制，所以还没有直接从官网把数据抓下来。
下一步需要允许我访问这些公开网站，或由你本机浏览器辅助下载后放到 `data/raw/`。
