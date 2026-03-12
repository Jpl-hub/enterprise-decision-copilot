<template>
  <div class="page-stack workbench-page refined-workbench">
    <PagePanel title="企业分析" eyebrow="单企业判断">
      <template #actions>
        <div class="toolbar-cluster">
          <label class="console-field">
            <select v-model="selectedCode" class="select-input toolbar-select">
              <option v-for="item in targets" :key="item.company_code" :value="item.company_code">{{ item.company_name }}</option>
            </select>
          </label>
          <button class="button-primary" @click="loadAll">刷新</button>
        </div>
      </template>

      <div v-if="loadError" class="error-box">
        {{ loadError }}
      </div>

      <section v-if="isBootstrapping" class="sub-panel workbench-loading-shell">
        <div class="workbench-loading-copy">
          <div class="spinner-placeholder"></div>
          <div>
            <strong>正在整理企业判断</strong>
            <p>系统正在汇总财报、研报、风险信号与图表锚点。</p>
          </div>
        </div>
        <div class="workbench-loading-grid">
          <div class="workbench-loading-card"></div>
          <div class="workbench-loading-card"></div>
          <div class="workbench-loading-card"></div>
        </div>
      </section>

      <div class="analysis-hero compact-analysis-hero" v-if="report">
        <div class="analysis-hero-main">
          <h3>{{ report.company_name }}</h3>
          <p class="panel-description strong-copy">{{ report.summary }}</p>
        </div>
        <div class="analysis-hero-metrics" v-if="risk">
          <div class="mini-metric-card">
            <span>风险等级</span>
            <strong :class="risk.risk_level === '高' ? 'text-danger' : 'text-primary'">{{ risk.risk_level }}</strong>
          </div>
          <div class="mini-metric-card">
            <span>风险分</span>
            <strong class="text-brand">{{ risk.risk_score }}</strong>
          </div>
          <div class="mini-metric-card" v-if="risk.model_prediction">
            <span>AI 模型概率</span>
            <strong class="text-brand">{{ formatPercent(risk.model_prediction.high_risk_probability) }}</strong>
          </div>
        </div>
      </div>

      <div v-if="report || brief || risk" class="company-metrics-grid analysis-signal-grid">
        <div class="company-metric-card">
          <span>财报基准口径</span>
          <strong>{{ report ? `${report.report_year} 年报` : '加载中' }}</strong>
        </div>
        <div class="company-metric-card">
          <span>历史趋势区间</span>
          <strong>{{ trendYearsText }}</strong>
        </div>
        <div class="company-metric-card">
          <span>个股研报证据</span>
          <strong>{{ stockEvidenceCount }} 条</strong>
        </div>
        <div class="company-metric-card">
          <span>行业对比证据</span>
          <strong>{{ industryEvidenceCount }} 条</strong>
        </div>
        <div class="company-metric-card">
          <span>宏观信号窗口</span>
          <strong>{{ macroWindowText }}</strong>
        </div>
        <div class="company-metric-card">
          <span>风险监测事项</span>
          <strong :class="monitoringCount > 0 ? 'text-danger' : ''">{{ monitoringCount }} 项</strong>
        </div>
      </div>

      <section v-if="report || brief || risk" class="sub-panel workbench-closure-strip">
        <div class="workbench-closure-main">
          <div class="trace-title-row">
            <strong>业务分析闭环</strong>
            <span class="badge-subtle">{{ closureEvidenceText }}</span>
          </div>
          <p>{{ closureSummaryText }}</p>
        </div>
        <div class="workbench-action-strip">
          <RouterLink to="/" class="button-primary">继续追问</RouterLink>
          <RouterLink :to="compareRoute" class="button-ghost">发起核心企业对比</RouterLink>
          <RouterLink :to="`/competition/${selectedCode}`" class="button-ghost">导出分析材料</RouterLink>
          <a v-if="financialSourceUrl" :href="financialSourceUrl" target="_blank" rel="noreferrer" class="button-ghost">查看财报原文</a>
        </div>
      </section>

      <section v-if="reasoningCards.length" class="workbench-reasoning-grid">
        <article v-for="item in reasoningCards" :key="item.title" class="sub-panel compact-data-panel">
          <div class="trace-title-row">
            <strong>{{ item.title }}</strong>
            <span class="badge-subtle">{{ item.badge }}</span>
          </div>
          <p class="workbench-reasoning-text">{{ item.summary }}</p>
          <div v-if="item.points.length" class="stack-list top-gap">
            <div v-for="point in item.points" :key="`${item.title}-${point}`" class="action-line-card">
              <p>{{ point }}</p>
            </div>
          </div>
        </article>
      </section>

      <div v-if="!isBootstrapping" class="analysis-grid two-main-one-side">
        <div class="analysis-main-stack">
          <div class="sub-panel content-panel">
            <div class="sub-panel-header">
              <h3>经营判断</h3>
            </div>
            <div v-if="briefLoading" class="empty-state">
              <div class="spinner-placeholder"></div>
              <p>正在整理判断依据...</p>
            </div>
            <div v-else-if="brief" class="stack-list">
              <div class="info-card compact emphasis-card brand-glow">
                <strong>{{ brief.verdict }}</strong>
                <p>{{ brief.summary }}</p>
              </div>
              <div class="info-card compact">
                <strong>核心判断依据</strong>
                <ul class="bullet-list">
                   <li v-for="j in brief.key_judgements" :key="j">{{ j }}</li>
                </ul>
              </div>
              <div class="info-card compact">
                <strong>建议执行动作</strong>
                <ul class="bullet-list">
                   <li v-for="a in brief.action_recommendations" :key="a">{{ a }}</li>
                </ul>
              </div>
              <div v-if="brief.evidence_highlights?.length" class="info-card compact">
                <strong>核心证据摘要</strong>
                <ul class="bullet-list">
                   <li v-for="e in brief.evidence_highlights.slice(0, 3)" :key="e">{{ e }}</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="sub-panel content-panel">
            <div class="sub-panel-header">
              <h3>经营拆解</h3>
            </div>
            <div v-if="reportLoading" class="empty-state">
              <div class="spinner-placeholder"></div>
              <p>正在汇总经营数据...</p>
            </div>
            <div v-else-if="report" class="stack-list">
              <div v-for="section in report.sections" :key="section.title" class="info-card compact section-card">
                <strong>{{ section.title }}</strong>
                <p>{{ section.content }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="analysis-side-stack">
          <div class="sub-panel side-panel">
            <div class="sub-panel-header">
              <h3>风险判断</h3>
            </div>
            <div v-if="riskLoading" class="empty-state">
              <div class="spinner-placeholder"></div>
              <p>正在校准风险信号...</p>
            </div>
            <div v-else-if="risk" class="stack-list">
              <div class="info-card compact" :class="risk.risk_level === '高' ? 'danger-glow' : ''">
                <strong>{{ risk.summary }}</strong>
                <p>规则评分 {{ risk.heuristic_score.toFixed(1) }} 分</p>
              </div>
              <div class="info-card compact" v-if="risk.model_prediction">
                <strong>风险模型</strong>
                <p>高风险概率 {{ formatPercent(risk.model_prediction.high_risk_probability) }} · 参考值 {{ formatMetric(risk.model_prediction.model_summary.metrics.roc_auc) }}</p>
              </div>
              <div class="info-card compact">
                <strong>主要风险驱动因素</strong>
                <ul class="bullet-list">
                   <li v-for="d in risk.drivers" :key="d">{{ d }}</li>
                </ul>
              </div>
              <div class="info-card compact" v-if="risk.monitoring_items?.length">
                <strong>持续监测事项清单</strong>
                <ul class="bullet-list">
                   <li v-for="m in risk.monitoring_items" :key="m" class="text-danger">{{ m }}</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="sub-panel side-panel">
            <div class="sub-panel-header">
              <h3>证据回链</h3>
              <span class="badge-subtle">{{ stockEvidenceCount + industryEvidenceCount }} 条关联</span>
            </div>
            <div class="stack-list evidence-dual-stack">
              <div class="info-card compact">
                <div class="trace-title-row">
                  <strong>相关个股研报</strong>
                  <span class="badge-subtle">{{ stockEvidenceCount }}</span>
                </div>
                <EvidenceList :items="stockEvidence" />
              </div>
              <div class="info-card compact">
                <div class="trace-title-row">
                  <strong>宏观与行业研报</strong>
                  <span class="badge-subtle">{{ industryEvidenceCount }}</span>
                </div>
                <EvidenceList :items="industryEvidence" />
              </div>
              <div class="info-card compact multimodal-evidence-card">
                <div class="trace-title-row">
                  <strong>多模态图表锚点</strong>
                  <span class="badge-subtle">{{ multimodalDigest?.filled_field_count || 0 }} 项识别</span>
                </div>
                <p class="workbench-inline-note">{{ multimodalDigest?.summary || '暂未识别到可用的财报页锚点。' }}</p>
                <div v-if="multimodalMetrics.length" class="selected-pill-group evidence-pill-cloud top-gap">
                  <span v-for="item in multimodalMetrics" :key="item.field" class="selected-pill">
                    {{ item.label }} <span class="text-brand">{{ item.display_value }}</span>
                  </span>
                </div>
                <div v-if="multimodalAssetLinks.length" class="page-anchor-row top-gap">
                  <a
                    v-for="item in multimodalAssetLinks"
                    :key="`${item.label}-${item.url || 'missing'}`"
                    class="page-anchor-link"
                    :href="item.url || financialSourceUrl"
                    target="_blank"
                    rel="noreferrer"
                  >
                    查看 {{ item.label }}
                  </a>
                </div>
              </div>
              <div class="info-card compact">
                <strong>本轮分析焦点</strong>
                <p class="workbench-inline-note">{{ queryTermsText }}</p>
                <div class="action-row" style="margin-top: 12px;">
                   <a v-if="financialSourceUrl" :href="financialSourceUrl" target="_blank" rel="noreferrer" class="text-link-button">打开财报源文件</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PagePanel>
  </div>
</template>

<style scoped>
.text-danger {
  color: var(--status-error) !important;
}
.text-primary {
  color: var(--text-primary) !important;
}
.text-brand {
  color: var(--brand-primary) !important;
}
.bullet-list {
  margin: 8px 0 0 16px;
  padding: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}
.bullet-list li {
  margin-bottom: 4px;
}
.emphasis-card p {
  line-height: 1.6;
}
.brand-glow {
  border-left: 3px solid var(--brand-primary);
  background: linear-gradient(to right, rgba(59, 130, 246, 0.05), transparent);
}
.danger-glow {
  border-left: 3px solid var(--status-error);
  background: linear-gradient(to right, rgba(239, 68, 68, 0.05), transparent);
}
.content-panel {
  background: var(--bg-surface-raised);
}
.side-panel {
  background: var(--bg-surface);
}
.spinner-placeholder {
  width: 32px;
  height: 32px;
  margin: 0 auto 16px;
  border-radius: 50%;
  border: 3px solid var(--border-subtle);
  border-top-color: var(--brand-primary);
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.workbench-loading-shell {
  display: grid;
  gap: 18px;
}
.workbench-loading-copy {
  display: flex;
  align-items: center;
  gap: 16px;
}
.workbench-loading-copy strong {
  display: block;
  margin-bottom: 4px;
}
.workbench-loading-copy p {
  margin: 0;
  color: var(--text-secondary);
}
.workbench-loading-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}
.workbench-loading-card {
  min-height: 132px;
  border-radius: 18px;
  background: linear-gradient(90deg, rgba(12, 27, 51, 0.04), rgba(12, 27, 51, 0.1), rgba(12, 27, 51, 0.04));
  background-size: 200% 100%;
  animation: shimmer 1.2s linear infinite;
}
.workbench-inline-note {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
@media (max-width: 900px) {
  .workbench-loading-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, RouterLink } from 'vue-router';

import { api } from '../api/client';
import type {
  CompanyReportResponse,
  DecisionBriefResponse,
  MultimodalAssetLink,
  MultimodalEvidenceDigest,
  MultimodalMetricItem,
  RiskForecastResponse,
} from '../api/types';
import EvidenceList from '../components/EvidenceList.vue';
import PagePanel from '../components/PagePanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';
import { useDashboardStore } from '../stores/dashboard';

const props = defineProps<{ companyCode?: string }>();
const route = useRoute();
const store = useDashboardStore();
const agentStore = useAgentThreadStore();
const selectedCode = ref(props.companyCode || String(route.params.companyCode || ''));
const loadError = ref('');
const report = ref<CompanyReportResponse | null>(null);
const brief = ref<DecisionBriefResponse | null>(null);
const risk = ref<RiskForecastResponse | null>(null);
const reportLoading = ref(false);
const briefLoading = ref(false);
const riskLoading = ref(false);
const hasLoadedOnce = ref(false);

const targets = computed(() => store.targets);
const stockEvidence = computed(() => brief.value?.evidence?.semantic_stock_reports || []);
const industryEvidence = computed(() => brief.value?.evidence?.semantic_industry_reports || []);
const stockEvidenceCount = computed(() => stockEvidence.value.length);
const industryEvidenceCount = computed(() => industryEvidence.value.length);
const monitoringCount = computed(() => risk.value?.monitoring_items?.length || 0);
const financialSourceUrl = computed(() => {
  const source = brief.value?.evidence?.financial_source_url;
  return typeof source === 'string' ? source : '';
});
const queryTermsText = computed(() => {
  const queryTerms = brief.value?.evidence?.query_terms || [];
  return queryTerms.length ? queryTerms.join('、') : '财报、研报、风险';
});
const trendYearsText = computed(() => {
  const trend = (report.value?.evidence?.trend_digest || {}) as Record<string, unknown>;
  const start = trend.start_year;
  const end = trend.end_year;
  return typeof start === 'number' && typeof end === 'number' ? `${start}-${end}` : '待补齐';
});
const macroWindowText = computed(() => {
  const macroItems = (report.value?.evidence?.macro_items || []) as Array<Record<string, unknown>>;
  if (!macroItems.length) return '待补齐';
  const first = macroItems[0];
  const name = typeof first.indicator_name === 'string' ? first.indicator_name : '宏观指标';
  const value = first.indicator_value;
  const unit = typeof first.unit === 'string' ? first.unit : '';
  return `${name}${value ?? ''}${unit}`;
});
const multimodalDigest = computed<MultimodalEvidenceDigest | null>(() => {
  const digest = report.value?.evidence?.multimodal_digest as MultimodalEvidenceDigest | undefined;
  return digest && typeof digest === 'object' ? digest : null;
});
const multimodalMetrics = computed<MultimodalMetricItem[]>(() => multimodalDigest.value?.metrics?.slice(0, 6) || []);
const multimodalAssetLinks = computed<MultimodalAssetLink[]>(() => multimodalDigest.value?.page_asset_links?.slice(0, 4) || []);
const closureEvidenceText = computed(() => {
  const evidenceCount = stockEvidenceCount.value + industryEvidenceCount.value;
  const multimodalCount = multimodalDigest.value?.filled_field_count || 0;
  return `研报 ${evidenceCount} 条 · 图表 ${multimodalCount} 项`;
});
const closureSummaryText = computed(() => {
  const riskLevel = risk.value?.risk_level || '待判断';
  const reportYear = report.value?.report_year ? `${report.value.report_year} 年报` : '财报待补齐';
  const disclosure = multimodalDigest.value?.published_at || '披露时间待补齐';
  return `${reportYear} 已进入当前企业闭环，当前判断为 ${riskLevel} 风险，最新财报锚点 ${disclosure}。`;
});
const isBootstrapping = computed(() => (
  !loadError.value &&
  !hasLoadedOnce.value &&
  (reportLoading.value || briefLoading.value || riskLoading.value || store.loading)
));
const reasoningCards = computed(() => {
  const cards: Array<{ title: string; badge: string; summary: string; points: string[] }> = [];
  if (report.value) {
    cards.push({
      title: '财报基线',
      badge: report.value.report_year ? `${report.value.report_year} 年报` : '官方财报',
      summary: report.value.summary,
      points: [
        `趋势区间 ${trendYearsText.value}`,
        `财报来源 ${financialSourceUrl.value ? '已回链' : '待补齐'}`,
        `多模态锚点 ${multimodalDigest.value?.available ? '已接入' : '待补齐'}`,
      ],
    });
  }
  if (brief.value) {
    cards.push({
      title: '管理判断链',
      badge: brief.value.verdict,
      summary: brief.value.summary,
      points: [
        `问题 ${brief.value.question}`,
        `关键词 ${queryTermsText.value}`,
        ...(brief.value.evidence_highlights?.slice(0, 2) || []),
      ],
    });
  }
  if (risk.value) {
    cards.push({
      title: '风险判断链',
      badge: risk.value.risk_level,
      summary: risk.value.summary,
      points: [
        `规则分 ${risk.value.heuristic_score.toFixed(1)}`,
        risk.value.model_prediction
          ? `模型概率 ${formatPercent(risk.value.model_prediction.high_risk_probability)}`
          : '模型概率 暂无',
        `监测项 ${monitoringCount.value} 项`,
      ],
    });
  }
  if (stockEvidenceCount.value || industryEvidenceCount.value || multimodalDigest.value?.available) {
    cards.push({
      title: '证据回链',
      badge: closureEvidenceText.value,
      summary: `个股研报 ${stockEvidenceCount.value} 条，行业研报 ${industryEvidenceCount.value} 条，多模态财报 ${multimodalDigest.value?.filled_field_count || 0} 项。`,
      points: [
        stockEvidence.value[0]?.title ? `最新个股研报 ${stockEvidence.value[0].title}` : '最新个股研报 暂无',
        industryEvidence.value[0]?.title ? `最新行业研报 ${industryEvidence.value[0].title}` : '最新行业研报 暂无',
        multimodalDigest.value?.page_refs?.length
          ? `图表页锚点 ${multimodalDigest.value.page_refs.slice(0, 3).join(' / ')}`
          : '图表页锚点 暂无',
      ],
    });
  }
  return cards;
});
const compareRoute = computed(() => {
  const rankingRows = (store.payload?.ranking || []) as Array<Record<string, unknown>>;
  const peerCode = rankingRows
    .map((item) => String(item.company_code || ''))
    .find((code) => code && code !== selectedCode.value);
  const companies = [selectedCode.value, peerCode || ''].filter(Boolean);
  return { path: '/compare', query: companies.length >= 2 ? { companies: companies.join(',') } : {} };
});

async function ensureTargets() {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  if (!selectedCode.value && store.targets.length) {
    selectedCode.value = props.companyCode || String(route.params.companyCode || store.targets[0].company_code);
  }
}

async function loadAll() {
  if (!selectedCode.value) return;
  reportLoading.value = true;
  briefLoading.value = true;
  riskLoading.value = true;
  loadError.value = '';
  try {
    const companyName = currentCompanyName();
    agentStore.setFocus(selectedCode.value, companyName);
    const [reportResult, briefResult, riskResult] = await Promise.all([
      api.getCompanyReport(selectedCode.value),
      api.getDecisionBrief(selectedCode.value, `结合财报、研报和风险模型，给出${companyName}的经营判断和动作建议`),
      api.getRiskForecast(selectedCode.value),
    ]);
    report.value = reportResult;
    brief.value = briefResult;
    risk.value = riskResult;
  } catch (error) {
    report.value = null;
    brief.value = null;
    risk.value = null;
    loadError.value = error instanceof Error ? error.message : '企业工作台加载失败';
  } finally {
    reportLoading.value = false;
    briefLoading.value = false;
    riskLoading.value = false;
    hasLoadedOnce.value = true;
  }
}

function currentCompanyName() {
  return (
    targets.value.find((item) => item.company_code === selectedCode.value)?.company_name ||
    report.value?.company_name ||
    brief.value?.company_name ||
    risk.value?.company_name ||
    agentStore.focusCompanyName ||
    '该企业'
  );
}

function formatPercent(value: number | null | undefined) {
  return value == null ? '暂无' : `${(value * 100).toFixed(1)}%`;
}

function formatMetric(value: number | null | undefined) {
  return value == null ? '暂无' : value.toFixed(3);
}

async function initializeWorkbench() {
  try {
    await ensureTargets();
    if (selectedCode.value) {
      await loadAll();
    }
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '企业工作台初始化失败';
  }
}

watch(() => props.companyCode, (value) => {
  if (value) selectedCode.value = value;
});
watch(selectedCode, () => {
  if (selectedCode.value) {
    void loadAll();
  }
});

onMounted(() => {
  void initializeWorkbench();
});
</script>
