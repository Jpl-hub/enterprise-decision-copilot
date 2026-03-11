# 分布式与大数据架构规划

## 当前落地形态

当前仓库先采用单机多进程的数据工程形态：

- 原始层：PDF / JSON / HTML / CSV
- 分层湖仓：Bronze / Silver / Gold
- 计算作业：Python 并行批处理
- 服务存储：SQLite

这样做的原因是：

- 本机即可稳定跑通
- 便于答辩现场演示
- 后续可平滑升级到真正的分布式引擎

## 下一阶段升级路线

### 存储层

- MinIO / HDFS：承载原始 PDF、HTML、JSON、Parquet
- 对象存储目录规范：`bronze/ silver/ gold/`

### 计算层

- Dask / Spark：批量清洗、去重、宽表构建、历史面板加工
- Airflow / Prefect：调度增量任务

### 服务层

- OLTP：PostgreSQL / MySQL
- OLAP：ClickHouse / DuckDB
- 检索：向量库或全文索引

## 比赛叙事

比赛版本不需要为了概念强行上整套集群，但必须体现：

- 分层存储思维
- 批量处理思维
- 可扩展到分布式的架构边界
- 数据质量治理与来源登记
