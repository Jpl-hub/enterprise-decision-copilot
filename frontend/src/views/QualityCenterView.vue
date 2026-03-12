<template>
  <div class="page-stack quality-page refined-quality-page">
    <PagePanel title="数据底座" eyebrow="Data Control Tower">
      <template #actions>
        <div class="toolbar-cluster">
          <button class="button-primary" @click="loadSummary" :disabled="loading">刷新</button>
        </div>
      </template>

      <div v-if="loading" class="empty-state">正在加载数据底座状态...</div>
      <template v-else-if="summary">
        <section class="control-tower-hero">
          <div class="tower-main-card">
            <div>
              <p class="section-tag">系统状态</p>
              <h3>{{ readinessHeadline }}</h3>
              <p>{{ readinessText }}</p>
            </div>
            <div class="tower-pill-row">
              <span class="tower-pill">财报 {{ percent(summary.official_report_coverage_ratio) }}</span>
              <span class="tower-pill">图表 {{ percent(summary.multimodal_extract_coverage_ratio) }}</span>
              <span class="tower-pill">提醒 {{ summary.pending_review_count }} 项</span>
            </div>
          </div>

          <div class="tower-side-grid">
            <div class="tower-stat-card">
              <span>核心样本</span>
              <strong>{{ summary.target_pool_ready ? '已就绪' : '未完成' }}</strong>
              <div class="signal-meter"><div class="signal-meter-fill" :style="{ width: `${summary.official_report_coverage_ratio * 100}%` }"></div></div>
            </div>
            <div class="tower-stat-card">
              <span>扩展样本</span>
              <strong>{{ summary.universe_report_downloaded_slots }}/{{ summary.universe_report_expected_slots }}</strong>
              <div class="signal-meter"><div class="signal-meter-fill accent" :style="{ width: `${summary.multimodal_extract_coverage_ratio * 100}%` }"></div></div>
            </div>
            <div class="tower-stat-card warning">
              <span>图表补全</span>
              <strong>{{ summary.multimodal_extract_report_count }}/{{ summary.multimodal_expected_report_count }}</strong>
              <div class="signal-meter"><div class="signal-meter-fill warning" :style="{ width: pendingWidth }"></div></div>
            </div>
          </div>
        </section>

        <section class="data-flow-board">
          <div class="flow-card">
            <span>官方财报</span>
            <strong>{{ summary.official_report_downloaded_slots }}/{{ summary.official_report_expected_slots }}</strong>
            <p>三所正式披露年报已进入主分析链路。</p>
          </div>
          <div class="flow-arrow">→</div>
          <div class="flow-card">
            <span>扩展样本</span>
            <strong>{{ summary.universe_report_downloaded_slots }}/{{ summary.universe_report_expected_slots }}</strong>
            <p>扩展企业池的年报下载进度，决定后续可扩到多大范围。</p>
          </div>
          <div class="flow-arrow">→</div>
          <div class="flow-card">
            <span>图表补全</span>
            <strong>{{ summary.multimodal_extract_report_count }}/{{ summary.multimodal_expected_report_count }}</strong>
            <p>复杂图表和表格是否已经补成结构化证据。</p>
          </div>
          <div class="flow-arrow">→</div>
          <div class="flow-card accent-card">
            <span>Agent 证据链</span>
            <strong>{{ summary.multimodal_backends.join(' / ') || '规则链路' }}</strong>
            <p>最终进入企业分析、对比和导出材料。</p>
          </div>
        </section>

        <section v-if="preparation" class="preparation-section">
          <div class="panel-split two-cols">
            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>数据准备度</h3>
                <span class="badge-subtle">{{ preparation.generated_at?.slice(0, 16).replace('T', ' ') || '实时快照' }}</span>
              </div>
              <div class="foundation-stat-grid">
                <div class="tower-stat-card">
                  <span>来源类型</span>
                  <strong>{{ preparation.source_count }}</strong>
                  <p>{{ preparation.processed_dataset_count }} 个 processed 数据集已落盘。</p>
                </div>
                <div class="tower-stat-card">
                  <span>企业池</span>
                  <strong>{{ preparation.target_pool_company_count }} / {{ preparation.universe_company_count }}</strong>
                  <p>核心企业池与外围企业池的当前规模。</p>
                </div>
                <div class="tower-stat-card">
                  <span>训练准备</span>
                  <strong>{{ preparation.multimodal_sft_sample_count }}</strong>
                  <p>多模态 SFT 样本，当前抽取 {{ preparation.multimodal_extract_count }} 份。</p>
                </div>
                <div class="tower-stat-card">
                  <span>扩样候选</span>
                  <strong>{{ preparation.selected_candidate_count }} / {{ preparation.promotion_candidate_count }}</strong>
                  <p>已排出的下一轮重点扩样企业。</p>
                </div>
              </div>
            </div>

            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>来源成熟度</h3>
                <span class="badge-subtle">{{ preparation.annual_years.join(' / ') || '年度待补齐' }}</span>
              </div>
              <div class="stack-list">
                <div v-for="item in preparation.source_status" :key="item.source_key" class="foundation-dataset-card">
                  <div class="trace-title-row">
                    <strong>{{ item.label }}</strong>
                    <span>{{ formatCount(item.rows) }} 行</span>
                  </div>
                  <p>最新 {{ item.latest || '待刷新' }}</p>
                  <span v-if="item.coverage_note" class="foundation-dataset-note">{{ item.coverage_note }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="panel-split two-cols">
            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>扩样候选</h3>
                <span class="badge-subtle">下一轮可拉升数据规模</span>
              </div>
              <div class="stack-list">
                <div v-for="item in preparation.top_candidates" :key="item.company_code" class="foundation-dataset-card">
                  <div class="trace-title-row">
                    <strong>{{ item.company_name }}</strong>
                    <span>{{ item.priority_score.toFixed(2) }}</span>
                  </div>
                  <p>{{ item.industry_name || '未分类' }} · 研报 {{ item.report_count }} 篇 · 机构 {{ item.institution_count }} 家</p>
                  <span v-if="item.latest_report_date" class="foundation-dataset-note">最新研报 {{ item.latest_report_date }}</span>
                </div>
              </div>
            </div>

            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>准备结论</h3>
                <span class="badge-subtle">先补这些</span>
              </div>
              <div class="stack-list">
                <div v-for="item in preparation.preparation_notes" :key="item" class="action-line-card">
                  <p>{{ item }}</p>
                </div>
              </div>
            </div>
          </div>

          <div v-if="preparation.promoted_exchange_status.length || preparation.promoted_companies.length" class="panel-split two-cols">
            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>扩样执行结果</h3>
                <span class="badge-subtle">{{ preparation.promotion_years.join(' / ') || '年度样本' }}</span>
              </div>
              <div class="foundation-stat-grid">
                <div class="tower-stat-card">
                  <span>已下载年报</span>
                  <strong>{{ preparation.promoted_report_download_count }}</strong>
                  <p>首批扩样企业已进入仓内的正式年报 PDF 数量。</p>
                </div>
                <div class="tower-stat-card">
                  <span>待补年份</span>
                  <strong>{{ preparation.promoted_report_missing_count }}</strong>
                  <p>还缺正式年报的年份槽位，后续需要继续补采。</p>
                </div>
                <div class="tower-stat-card">
                  <span>完整企业</span>
                  <strong>{{ preparation.promoted_ready_company_count }}</strong>
                  <p>扩样首批里已经覆盖所有目标年份的企业。</p>
                </div>
                <div class="tower-stat-card">
                  <span>部分就绪</span>
                  <strong>{{ preparation.promoted_partial_company_count }}</strong>
                  <p>已有真实年报，但还没有补齐全部年份。</p>
                </div>
              </div>

              <div class="stack-list top-gap">
                <div v-for="item in preparation.promoted_exchange_status" :key="item.exchange" class="foundation-dataset-card">
                  <div class="trace-title-row">
                    <strong>{{ formatExchange(item.exchange) }}</strong>
                    <span>{{ item.downloaded_reports }} / {{ item.downloaded_reports + item.missing_reports }}</span>
                  </div>
                  <p>已选企业 {{ item.selected_companies }} 家，当前待补 {{ item.missing_reports }} 份。</p>
                </div>
              </div>
            </div>

            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>首批扩样企业</h3>
                <span class="badge-subtle">真实下载状态</span>
              </div>
              <div class="stack-list">
                <div v-for="item in preparation.promoted_companies" :key="`${item.exchange}-${item.company_code}`" class="foundation-dataset-card">
                  <div class="trace-title-row">
                    <strong>{{ item.company_name }}</strong>
                    <span>{{ item.downloaded_reports }} / {{ preparation.promotion_years.length || 0 }}</span>
                  </div>
                  <p>{{ formatExchange(item.exchange) }} · {{ item.industry_name || '未分类' }} · 优先级 {{ item.priority_score.toFixed(2) }}</p>
                  <span class="foundation-dataset-note">
                    已下载 {{ formatYearList(item.downloaded_years) }}<span v-if="item.missing_years.length"> · 待补 {{ formatYearList(item.missing_years) }}</span>
                  </span>
                  <span v-if="item.latest_published_at" class="foundation-dataset-note">最新披露 {{ item.latest_published_at }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section v-if="governance" class="preparation-section">
          <div class="sub-panel compact-data-panel foundation-overview-panel">
            <div class="sub-panel-header">
              <h3>可信治理表</h3>
              <span class="badge-subtle">{{ governance.generated_at?.slice(0, 16).replace('T', ' ') || '实时快照' }}</span>
            </div>
            <p class="foundation-overview-text">
              这里直接回答“数据从哪来、覆盖到哪、哪些字段能不能信、系统结论依赖什么证据”，不是再写抽象说明。
            </p>
          </div>

          <div class="panel-split two-cols">
            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>数据源登记表</h3>
                <span class="badge-subtle">{{ governance.source_catalog.length }} 条</span>
              </div>
              <div class="stack-list">
                <div v-for="item in governance.source_catalog" :key="`${item.source_name}-${item.entry_url}`" class="foundation-dataset-card">
                  <div class="trace-title-row">
                    <strong>{{ item.source_name }}</strong>
                    <span>{{ item.priority }}</span>
                  </div>
                  <p>{{ item.domain }} · {{ item.usage_scope }}</p>
                  <span class="foundation-dataset-note">{{ item.compliance_note }}</span>
                  <a :href="item.entry_url" target="_blank" rel="noreferrer" class="text-link-button">查看入口</a>
                </div>
              </div>
            </div>

            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>企业覆盖表</h3>
                <span class="badge-subtle">{{ governance.company_coverage.length }} 家核心企业</span>
              </div>
              <div class="stack-list">
                <div v-for="item in governance.company_coverage" :key="item.company_code" class="foundation-dataset-card">
                  <div class="trace-title-row">
                    <strong>{{ item.company_name }}</strong>
                    <span>{{ formatExchange(item.exchange) }}</span>
                  </div>
                  <p>{{ item.industry || '未分类' }} · 年报 {{ item.annual_report_count }} 份 · 定期披露 {{ item.periodic_report_count }} 条</p>
                  <span class="foundation-dataset-note">
                    年份 {{ formatYearList(item.annual_years) }} · 研报 {{ item.research_report_count }} 条 · 多模态 {{ item.multimodal_extract_count }} 份
                  </span>
                  <span v-if="item.latest_disclosure" class="foundation-dataset-note">最新披露 {{ item.latest_disclosure }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="panel-split two-cols">
            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>字段质量表</h3>
                <span class="badge-subtle">按空值率排序</span>
              </div>
              <div class="stack-list">
                <div v-for="item in governance.field_quality" :key="`${item.dataset}-${item.field}`" class="foundation-dataset-card">
                  <div class="trace-title-row">
                    <strong>{{ item.dataset }} / {{ item.field }}</strong>
                    <span>{{ percent(item.null_ratio) }}</span>
                  </div>
                  <p>{{ item.source_type }} · {{ item.extraction_method }}</p>
                  <span class="foundation-dataset-note">{{ item.review_status }} · {{ item.usage_scope }}</span>
                </div>
              </div>
            </div>

            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>证据映射表</h3>
                <span class="badge-subtle">{{ governance.evidence_mapping.length }} 个模块</span>
              </div>
              <div class="stack-list">
                <div v-for="item in governance.evidence_mapping" :key="item.module" class="foundation-dataset-card">
                  <div class="trace-title-row">
                    <strong>{{ item.module }}</strong>
                    <span>{{ item.output_label }}</span>
                  </div>
                  <p>来源 {{ item.primary_sources.join(' / ') }}</p>
                  <span class="foundation-dataset-note">证据字段 {{ item.evidence_fields.join(' / ') }}</span>
                  <span class="foundation-dataset-note">{{ item.verification_rule }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section v-if="stack && (stackPillars.length || stackEngines.length)" class="system-blueprint-section">
          <div class="sub-panel compact-data-panel blueprint-summary-panel">
            <div class="sub-panel-header">
              <h3>系统蓝图</h3>
              <span class="badge-subtle">三条主线 · {{ stackGeneratedAt }}</span>
            </div>
            <p class="foundation-overview-text">
              这里不展示概念口号，只展示当前仓里已经落地的系统能力、短板和下一步。系统按“传统应用 + Agent / 深度学习 / 大数据计算”三条线同步推进。
            </p>

            <div v-if="stackPillars.length" class="blueprint-pillar-grid">
              <article v-for="pillar in stackPillars" :key="pillar.pillar_id" :class="['blueprint-pillar-card', pillar.status]">
                <div class="blueprint-pillar-head">
                  <div>
                    <span class="section-tag">{{ pillar.name }}</span>
                    <h4>{{ pillar.stage_label }}</h4>
                  </div>
                  <div class="blueprint-score-badge">
                    <strong>{{ formatReadiness(pillar.readiness_score) }}</strong>
                    <span>就绪度</span>
                  </div>
                </div>
                <div class="mini-bar-track top-gap">
                  <div class="mini-bar-fill blueprint-score-fill" :style="{ width: readinessWidth(pillar.readiness_score) }"></div>
                </div>
                <p>{{ pillar.summary }}</p>

                <div class="blueprint-pill-row">
                  <span
                    v-for="metric in pillar.headline_metrics"
                    :key="`${pillar.pillar_id}-${metric.label}`"
                    :class="['blueprint-metric-pill', `tone-${metric.tone}`]"
                  >
                    {{ metric.label }} {{ metric.value }}
                  </span>
                </div>

                <div class="stack-list top-gap">
                  <div class="action-line-card">
                    <strong>已成形</strong>
                    <p>{{ pillar.strengths[0] }}</p>
                  </div>
                  <div class="action-line-card">
                    <strong>当前缺口</strong>
                    <p>{{ pillar.gaps[0] }}</p>
                  </div>
                  <div class="action-line-card">
                    <strong>下一步</strong>
                    <p>{{ pillar.next_steps[0] }}</p>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <div class="panel-split two-cols blueprint-detail-grid">
            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>关键引擎</h3>
                <span class="badge-subtle">{{ stackEngines.length }} 个模块</span>
              </div>
              <div class="blueprint-engine-grid">
                <article v-for="engine in stackEngines" :key="engine.engine_id" :class="['blueprint-engine-card', engine.status]">
                  <div class="trace-title-row">
                    <strong>{{ engine.name }}</strong>
                    <span>{{ formatReadiness(engine.readiness_score || 0) }}</span>
                  </div>
                  <p class="engine-category-line">{{ engine.category }} · {{ engine.stage_label || '状态同步中' }}</p>
                  <p>{{ engine.role }}</p>
                  <div class="blueprint-engine-metrics">
                    <span
                      v-for="metric in engine.headline_metrics"
                      :key="`${engine.engine_id}-${metric.label}`"
                      :class="['blueprint-metric-pill', 'compact', `tone-${metric.tone}`]"
                    >
                      {{ metric.label }} {{ metric.value }}
                    </span>
                  </div>
                  <span v-if="engine.gaps.length" class="foundation-dataset-note">缺口：{{ engine.gaps[0] }}</span>
                </article>
              </div>
            </div>

            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>系统判断</h3>
                <span class="badge-subtle">设计逻辑</span>
              </div>
              <div class="stack-list">
                <div v-for="item in stackStory" :key="item" class="action-line-card">
                  <p>{{ item }}</p>
                </div>
              </div>
              <div class="sub-panel-header top-gap">
                <h3>下一阶段工程动作</h3>
                <span class="badge-subtle">按这个顺序做</span>
              </div>
              <div class="stack-list">
                <div v-for="item in stackActions" :key="item" class="action-line-card">
                  <p>{{ item }}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section v-if="foundation" class="foundation-section">
          <div class="sub-panel compact-data-panel foundation-overview-panel">
            <div class="sub-panel-header">
              <h3>湖仓与计算引擎</h3>
              <span class="badge-subtle">{{ foundation.warehouse_table_count }} 张表视图</span>
            </div>

            <div class="foundation-stat-grid">
              <div class="tower-stat-card">
                <span>仓内总行数</span>
                <strong>{{ formatCount(foundation.total_warehouse_rows) }}</strong>
                <p>Bronze / Silver / Gold 统一进入 DuckDB mart。</p>
              </div>
              <div class="tower-stat-card">
                <span>CSV 产物</span>
                <strong>{{ foundation.csv_artifact_count }}</strong>
                <p>原始与清洗链路均保留可追溯落盘。</p>
              </div>
              <div class="tower-stat-card">
                <span>Parquet 产物</span>
                <strong>{{ foundation.parquet_artifact_count }}</strong>
                <p>便于后续接入更大规模批处理与分析引擎。</p>
              </div>
              <div class="tower-stat-card">
                <span>官方 PDF 清单</span>
                <strong>{{ foundation.official_inventory_rows }}</strong>
                <p>真实披露下载与抽取链路的入口样本。</p>
              </div>
            </div>

            <div class="foundation-layer-grid">
              <div v-for="item in foundation.lake_layers" :key="item.layer" class="foundation-layer-card">
                <span>{{ formatLayer(item.layer) }}</span>
                <strong>{{ item.table_count }} 张表</strong>
                <p>{{ formatCount(item.row_count) }} 行</p>
              </div>
            </div>

            <div class="tower-pill-row foundation-mart-row">
              <span v-for="item in foundation.mart_views.slice(0, 6)" :key="item" class="tower-pill">{{ item }}</span>
            </div>
          </div>

          <div class="panel-split two-cols foundation-detail-grid">
            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>空值热点</h3>
                <span class="badge-subtle">治理优先级</span>
              </div>
              <div class="stack-list">
                <div v-for="item in foundation.top_null_fields" :key="`${item.table}-${item.field}`" class="foundation-hotspot-card">
                  <div class="trace-title-row">
                    <strong>{{ item.table }} / {{ item.field }}</strong>
                    <span>{{ percent(item.null_ratio) }}</span>
                  </div>
                  <div class="mini-bar-track">
                    <div class="mini-bar-fill warning" :style="{ width: `${Math.max(12, item.null_ratio * 100)}%` }"></div>
                  </div>
                </div>
              </div>
            </div>

            <div class="sub-panel compact-data-panel">
              <div class="sub-panel-header">
                <h3>主题数据集</h3>
                <span class="badge-subtle">规模与缺口</span>
              </div>
              <div class="stack-list">
                <div v-for="item in foundation.dataset_profiles.slice(0, 6)" :key="item.table" class="foundation-dataset-card">
                  <div class="trace-title-row">
                    <strong>{{ item.table }}</strong>
                    <span>{{ formatCount(item.rows) }} 行</span>
                  </div>
                  <p>{{ item.columns }} 列 · 重复 {{ item.duplicate_rows }} 条 · 最高空值 {{ percent(item.max_null_ratio) }}</p>
                  <span v-if="item.hotspot_fields.length" class="foundation-dataset-note">
                    热点字段：{{ item.hotspot_fields.map((field) => `${field.field} ${percent(field.null_ratio)}`).join(' · ') }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section v-if="periodCoverage.length" class="freshness-section">
          <div class="sub-panel compact-data-panel freshness-panel">
            <div class="sub-panel-header">
              <h3>定期披露覆盖</h3>
              <span class="badge-subtle">{{ latestDisclosureLine }}</span>
            </div>
            <div class="freshness-period-grid">
              <div v-for="period in periodCoverage" :key="period.period_type" class="freshness-period-card">
                <div class="freshness-period-head">
                  <strong>{{ period.period_label }}</strong>
                  <span class="badge-subtle">{{ period.covered_companies }}/{{ targetPoolCount }}</span>
                </div>
                <div class="mini-bar-track">
                  <div class="mini-bar-fill freshness-bar-fill" :style="{ width: `${Math.max(12, period.coverage_ratio * 100)}%` }"></div>
                </div>
                <p>{{ percent(period.coverage_ratio) }} 覆盖，最新 {{ period.latest_company_name || '暂无' }}</p>
                <span class="freshness-period-meta">{{ period.latest_published_at || '暂无披露日期' }}</span>
              </div>
            </div>
          </div>
        </section>

        <div class="panel-split two-cols">
          <div class="sub-panel compact-data-panel">
            <div class="sub-panel-header">
              <h3>交易所接入</h3>
              <span class="badge-subtle">三所运行态</span>
            </div>
            <div class="stack-list">
              <div v-for="item in summary.exchange_status" :key="item.exchange" class="exchange-board-card">
                <div class="trace-title-row">
                  <strong>{{ formatExchange(item.exchange) }}</strong>
                  <span>{{ item.downloaded_rows }}/{{ item.rows }}</span>
                </div>
                <div class="signal-meter top-gap"><div class="signal-meter-fill dark" :style="{ width: exchangeWidth(item) }"></div></div>
                <div class="exchange-board-meta">
                  <span>Manifest {{ item.manifest_exists ? '已就绪' : '缺失' }}</span>
                  <span>文件缺失 {{ item.file_missing_rows }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="sub-panel compact-data-panel">
            <div class="sub-panel-header">
              <h3>当前缺口</h3>
              <span class="badge-subtle">先看这些</span>
            </div>
            <div class="stack-list">
              <div class="anomaly-heat-card">
                <div class="trace-title-row">
                  <strong>缺报告</strong>
                  <span>{{ summary.issue_breakdown.missing_reports }} 项</span>
                </div>
                <p>主样本或扩展样本里，仍未下载到位的官方年报。</p>
              </div>
              <div class="anomaly-heat-card">
                <div class="trace-title-row">
                  <strong>字段缺口</strong>
                  <span>{{ summary.issue_breakdown.field_gaps }} 项</span>
                </div>
                <p>关键字段缺失或版式异常，可能影响经营与风险判断。</p>
              </div>
              <div class="anomaly-heat-card">
                <div class="trace-title-row">
                  <strong>图表待补</strong>
                  <span>{{ summary.issue_breakdown.multimodal_missing }} 项</span>
                </div>
                <p>已下载年报但还没有完成图表与表格补全。</p>
              </div>
              <div class="anomaly-heat-card">
                <div class="trace-title-row">
                  <strong>图表偏少</strong>
                  <span>{{ summary.issue_breakdown.multimodal_low_coverage }} 项</span>
                </div>
                <p>已做图表补全，但识别字段仍然偏少。</p>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-split two-cols">
          <div class="sub-panel compact-data-panel">
            <div class="sub-panel-header">
              <h3>图表抽取进展</h3>
              <span class="badge-subtle">多模态</span>
            </div>
            <div v-if="recentExtracts.length" class="stack-list">
              <div v-for="item in summary.multimodal_recent_extracts.slice(0, 4)" :key="`${item.company_code}-${item.report_year}`" class="multimodal-board-card">
                <div class="trace-title-row">
                  <strong>{{ item.company_name || item.company_code }}</strong>
                  <span>{{ item.backend }}</span>
                </div>
                <div class="mini-bar-item top-gap">
                  <div class="mini-bar-head">
                    <span>字段补全</span>
                    <strong>{{ item.filled_field_count }}</strong>
                  </div>
                  <div class="mini-bar-track"><div class="mini-bar-fill" :style="{ width: multimodalFieldWidth(item.filled_field_count) }"></div></div>
                </div>
                <p>页面 {{ item.page_images.length }} 张 · {{ item.notes.join('；') || '已进入证据链' }}</p>
              </div>
            </div>
            <div v-else class="stack-list">
              <div v-for="item in multimodalFallbackCards" :key="item.title" class="multimodal-board-card">
                <div class="trace-title-row">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.value }}</span>
                </div>
                <p>{{ item.detail }}</p>
              </div>
            </div>
          </div>

          <div class="sub-panel compact-data-panel">
            <div class="sub-panel-header">
              <h3>可信度判断</h3>
              <span class="badge-subtle">当前建议</span>
            </div>
            <div class="stack-list">
              <div v-for="item in confidenceNotes" :key="item" class="action-line-card"><p>{{ item }}</p></div>
            </div>
          </div>
        </div>
      </template>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { api } from '../api/client';
import type {
  AIStackSummaryResponse,
  DataFoundationSummaryResponse,
  DataGovernanceSummaryResponse,
  DataPreparationSummaryResponse,
  ExchangeQualityStatus,
  QualitySummaryResponse,
} from '../api/types';
import PagePanel from '../components/PagePanel.vue';
import { useDashboardStore } from '../stores/dashboard';

const loading = ref(false);
const summary = ref<QualitySummaryResponse | null>(null);
const foundation = ref<DataFoundationSummaryResponse | null>(null);
const governance = ref<DataGovernanceSummaryResponse | null>(null);
const preparation = ref<DataPreparationSummaryResponse | null>(null);
const stack = ref<AIStackSummaryResponse | null>(null);
const dashboardStore = useDashboardStore();

const readinessHeadline = computed(() => {
  if (!summary.value) return '加载中';
  if (!summary.value.target_pool_ready) return '核心样本还没有全部就绪';
  if (summary.value.multimodal_extract_coverage_ratio < 0.5) return '核心样本可用，但图表补全还没有做完';
  if (summary.value.universe_report_coverage_ratio < 0.9) return '核心样本可用，扩展样本仍在补齐';
  return '数据底座已进入稳定运行';
  return '数据底座正在持续扩充';
});

const readinessText = computed(() => {
  if (!summary.value) return '正在汇总';
  return `核心样本 ${summary.value.official_report_downloaded_slots}/${summary.value.official_report_expected_slots}，扩展样本 ${summary.value.universe_report_downloaded_slots}/${summary.value.universe_report_expected_slots}，图表补全 ${summary.value.multimodal_extract_report_count}/${summary.value.multimodal_expected_report_count}。`;
});

const recentExtracts = computed(() => summary.value?.multimodal_recent_extracts || []);
const stackGeneratedAt = computed(() => {
  const value = stack.value?.generated_at;
  return typeof value === 'string' && value ? value.slice(0, 16).replace('T', ' ') : '系统快照';
});
const stackPillars = computed(() => (Array.isArray(stack.value?.pillars) ? stack.value?.pillars || [] : []));
const stackEngines = computed(() => (Array.isArray(stack.value?.engines) ? stack.value?.engines || [] : []));
const stackStory = computed(() => (Array.isArray(stack.value?.system_story) ? stack.value?.system_story || [] : []));
const stackActions = computed(() => (Array.isArray(stack.value?.priority_actions) ? stack.value?.priority_actions || [] : []));
const periodCoverage = computed(() => dashboardStore.payload?.freshness?.period_summaries || []);
const targetPoolCount = computed(() => dashboardStore.targets.length || summary.value?.target_pool_company_count || 0);
const latestDisclosureLine = computed(() => {
  const freshness = dashboardStore.payload?.freshness;
  if (!freshness?.latest_official_disclosure) return '真实披露';
  return `${freshness.latest_periodic_label || '年报'} 更新到 ${freshness.latest_official_disclosure}`;
});

const confidenceNotes = computed(() => {
  if (!summary.value) return [];
  const notes = [
    `核心样本已覆盖 ${summary.value.official_report_downloaded_slots}/${summary.value.official_report_expected_slots}，主分析链路可以先围绕这些企业展开。`,
    `扩展样本当前是 ${summary.value.universe_report_downloaded_slots}/${summary.value.universe_report_expected_slots}，后续大范围对比还要继续补齐。`,
  ];
  if (summary.value.multimodal_extract_coverage_ratio < 0.5) {
    notes.push('图表补全还不够，遇到复杂图表型问题时需要谨慎引用。');
  } else if (summary.value.universe_report_coverage_ratio < 0.9) {
    notes.push('主样本可用，但扩展企业池还没有完全补齐。');
  } else {
    notes.push('核心样本、扩展样本和图表补全都已进入可用区间。');
  }
  return notes;
});

const multimodalFallbackCards = computed(() => {
  if (!summary.value || recentExtracts.value.length) return [];
  const backendLabel = summary.value.multimodal_backends.join(' / ') || '规则链路';
  return [
    {
      title: '待补任务',
      value: `${summary.value.issue_breakdown.multimodal_missing} 项`,
      detail: '优先补齐核心样本年报中的复杂图表、经营分部表和风险提示页，避免复杂问题只剩文本结论。',
    },
    {
      title: '当前引擎',
      value: backendLabel,
      detail: '这部分代表图表抽取将由哪些链路负责，后续要把多模态结果真正送进企业分析和对比证据流。',
    },
    {
      title: '引用策略',
      value: summary.value.multimodal_extract_coverage_ratio < 0.5 ? '谨慎引用' : '逐步放开',
      detail: '在近期抽取样本为空时，页面直接展示治理优先级，避免控制塔区域出现空白。',
    },
  ];
});

const pendingWidth = computed(() => `${Math.min(100, Math.max(12, (summary.value?.pending_review_count || 0) * 10))}%`);

function percent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatCount(value: number) {
  return Intl.NumberFormat('zh-CN').format(value || 0);
}

function formatExchange(value: string) {
  const labels: Record<string, string> = { SSE: '上交所', SZSE: '深交所', BSE: '北交所' };
  return labels[String(value || '').toUpperCase()] || value;
}

function formatLayer(value: string) {
  const labels: Record<string, string> = {
    bronze: 'Bronze 原始层',
    silver: 'Silver 清洗层',
    gold: 'Gold 主题层',
  };
  return labels[String(value || '').toLowerCase()] || value;
}

function exchangeWidth(item: ExchangeQualityStatus) {
  if (!item.rows) return '8%';
  return `${Math.max(10, (item.downloaded_rows / item.rows) * 100)}%`;
}

function multimodalFieldWidth(count: number) {
  return `${Math.min(100, Math.max(12, count * 4))}%`;
}

function formatReadiness(value: number) {
  return `${Math.round((value || 0) * 100)}`;
}

function readinessWidth(value: number) {
  return `${Math.max(12, Math.min(100, (value || 0) * 100))}%`;
}

function formatYearList(values: number[]) {
  if (!values.length) return '暂无';
  return values.join(' / ');
}

async function loadSummary() {
  loading.value = true;
  try {
    const [governanceSummary, qualitySummary, foundationSummary, preparationSummary, aiStack] = await Promise.all([
      api.getQualityGovernance(),
      api.getQualitySummary(),
      api.getQualityFoundation(),
      api.getQualityPreparation(),
      api.getAIStack(),
      dashboardStore.payload ? Promise.resolve(dashboardStore.payload) : dashboardStore.load(),
    ]);
    governance.value = governanceSummary;
    summary.value = qualitySummary;
    foundation.value = foundationSummary;
    preparation.value = preparationSummary;
    stack.value = aiStack;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadSummary();
});
</script>
