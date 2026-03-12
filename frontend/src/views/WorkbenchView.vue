<template>
  <div class="page-stack workbench-page refined-workbench">
    <PagePanel title="企业分析" eyebrow="Enterprise Detail">
      <template #actions>
        <div class="toolbar-cluster">
          <select v-model="selectedCode" class="select-input toolbar-select">
            <option v-for="item in targets" :key="item.company_code" :value="item.company_code">{{ item.company_name }}</option>
          </select>
          <button class="button-primary" @click="loadAll">刷新</button>
        </div>
      </template>

      <div v-if="loadError" class="error-banner">
        {{ loadError }}
      </div>

      <div class="analysis-hero compact-analysis-hero" v-if="report">
        <div class="analysis-hero-main">
          <h3>{{ report.company_name }}</h3>
          <p class="panel-description strong-copy">{{ report.summary }}</p>
        </div>
        <div class="analysis-hero-metrics" v-if="risk">
          <div class="mini-metric-card">
            <span>风险等级</span>
            <strong>{{ risk.risk_level }}</strong>
          </div>
          <div class="mini-metric-card">
            <span>风险分</span>
            <strong>{{ risk.risk_score }}</strong>
          </div>
          <div class="mini-metric-card" v-if="risk.model_prediction">
            <span>模型概率</span>
            <strong>{{ formatPercent(risk.model_prediction.high_risk_probability) }}</strong>
          </div>
        </div>
      </div>

      <div v-if="report || brief || risk" class="company-metrics-grid analysis-signal-grid">
        <div class="company-metric-card">
          <span>财报口径</span>
          <strong>{{ report ? `${report.report_year} 年报` : '加载中' }}</strong>
        </div>
        <div class="company-metric-card">
          <span>趋势区间</span>
          <strong>{{ trendYearsText }}</strong>
        </div>
        <div class="company-metric-card">
          <span>个股研报证据</span>
          <strong>{{ stockEvidenceCount }} 条</strong>
        </div>
        <div class="company-metric-card">
          <span>行业证据</span>
          <strong>{{ industryEvidenceCount }} 条</strong>
        </div>
        <div class="company-metric-card">
          <span>宏观窗口</span>
          <strong>{{ macroWindowText }}</strong>
        </div>
        <div class="company-metric-card">
          <span>风险监测项</span>
          <strong>{{ monitoringCount }} 项</strong>
        </div>
      </div>

      <section v-if="report || brief || risk" class="sub-panel workbench-closure-strip">
        <div class="workbench-closure-main">
          <div class="trace-title-row">
            <strong>分析闭环</strong>
            <span class="badge-subtle">{{ closureEvidenceText }}</span>
          </div>
          <p>{{ closureSummaryText }}</p>
        </div>
        <div class="workbench-action-strip">
          <RouterLink to="/" class="button-primary">继续追问</RouterLink>
          <RouterLink :to="compareRoute" class="button-ghost">企业对比</RouterLink>
          <RouterLink :to="`/competition/${selectedCode}`" class="button-ghost">导出报告</RouterLink>
          <a v-if="financialSourceUrl" :href="financialSourceUrl" target="_blank" rel="noreferrer" class="button-ghost">财报原文</a>
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

      <div class="analysis-grid two-main-one-side">
        <div class="analysis-main-stack">
          <div class="sub-panel">
            <div class="sub-panel-header">
              <h3>管理判断</h3>
            </div>
            <div v-if="briefLoading" class="empty-state">正在生成判断...</div>
            <div v-else-if="brief" class="stack-list">
              <div class="info-card compact emphasis-card">
                <strong>{{ brief.verdict }}</strong>
                <p>{{ brief.summary }}</p>
              </div>
              <div class="info-card compact">
                <strong>关键判断</strong>
                <p>{{ brief.key_judgements.join('；') }}</p>
              </div>
              <div class="info-card compact">
                <strong>建议动作</strong>
                <p>{{ brief.action_recommendations.join('；') }}</p>
              </div>
              <div v-if="brief.evidence_highlights?.length" class="info-card compact">
                <strong>证据摘要</strong>
                <p>{{ brief.evidence_highlights.slice(0, 3).join('；') }}</p>
              </div>
            </div>
          </div>

          <div class="sub-panel">
            <h3>经营分析</h3>
            <div v-if="reportLoading" class="empty-state">正在生成分析...</div>
            <div v-else-if="report" class="stack-list">
              <div v-for="section in report.sections" :key="section.title" class="info-card compact section-card">
                <strong>{{ section.title }}</strong>
                <p>{{ section.content }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="analysis-side-stack">
          <div class="sub-panel">
            <h3>风险判断</h3>
            <div v-if="riskLoading" class="empty-state">正在生成风险预测...</div>
            <div v-else-if="risk" class="stack-list">
              <div class="info-card compact">
                <strong>{{ risk.summary }}</strong>
                <p>规则引擎 {{ risk.heuristic_score.toFixed(1) }} 分</p>
              </div>
              <div class="info-card compact" v-if="risk.model_prediction">
                <strong>AI 风险模型</strong>
                <p>高风险概率 {{ formatPercent(risk.model_prediction.high_risk_probability) }} · AUC {{ formatMetric(risk.model_prediction.model_summary.metrics.roc_auc) }}</p>
              </div>
              <div class="info-card compact">
                <strong>主要驱动</strong>
                <p>{{ risk.drivers.join('；') }}</p>
              </div>
              <div class="info-card compact" v-if="risk.monitoring_items?.length">
                <strong>持续监测</strong>
                <p>{{ risk.monitoring_items.join('；') }}</p>
              </div>
            </div>
          </div>

          <div class="sub-panel">
            <div class="sub-panel-header">
              <h3>证据回链</h3>
              <span class="badge-subtle">{{ stockEvidenceCount + industryEvidenceCount }} 条</span>
            </div>
            <div class="stack-list evidence-dual-stack">
              <div class="info-card compact">
                <div class="trace-title-row">
                  <strong>个股研报证据</strong>
                  <span>{{ stockEvidenceCount }}</span>
                </div>
                <EvidenceList :items="stockEvidence" />
              </div>
              <div class="info-card compact">
                <div class="trace-title-row">
                  <strong>行业研报证据</strong>
                  <span>{{ industryEvidenceCount }}</span>
                </div>
                <EvidenceList :items="industryEvidence" />
              </div>
              <div class="info-card compact multimodal-evidence-card">
                <div class="trace-title-row">
                  <strong>多模态财报锚点</strong>
                  <span>{{ multimodalDigest?.filled_field_count || 0 }} 项</span>
                </div>
                <p>{{ multimodalDigest?.summary || '当前企业尚未补齐多模态财报锚点，暂以结构化财务与研报证据为主。' }}</p>
                <div v-if="multimodalMetrics.length" class="selected-pill-group evidence-pill-cloud top-gap">
                  <span v-for="item in multimodalMetrics" :key="item.field" class="selected-pill">
                    {{ item.label }} {{ item.display_value }}
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
                    {{ item.label }}
                  </a>
                </div>
                <p v-if="multimodalDigest?.notes?.length" class="page-anchor-hint">{{ multimodalDigest.notes[0] }}</p>
              </div>
              <div class="info-card compact">
                <strong>证据关键词</strong>
                <p>{{ queryTermsText }}</p>
                <a v-if="financialSourceUrl" :href="financialSourceUrl" target="_blank" rel="noreferrer">查看财报原文</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PagePanel>
  </div>
</template>

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
  return queryTerms.length ? queryTerms.join('、') : '当前问题还没有明确证据关键词。';
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
