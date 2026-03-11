<template>
  <div class="page-stack">
    <PagePanel title="企业工作台" eyebrow="Workbench" description="围绕单家企业集中查看综合报告、决策简报、风险预测和 Agent 问答。">
      <template #actions>
        <select v-model="selectedCode" class="select-input">
          <option v-for="item in targets" :key="item.company_code" :value="item.company_code">{{ item.company_name }}</option>
        </select>
      </template>
      <div class="button-row">
        <button class="button-primary" @click="loadAll">刷新三类分析</button>
        <button class="button-ghost" @click="runAgent">运行 Agent 问答</button>
      </div>
      <div class="panel-split three-cols">
        <div class="sub-panel">
          <h3>综合报告</h3>
          <p v-if="reportLoading" class="empty-state">正在生成综合报告...</p>
          <div v-else-if="report" class="stack-list">
            <div v-for="section in report.sections" :key="section.title" class="info-card compact">
              <strong>{{ section.title }}</strong>
              <p class="muted">{{ section.content }}</p>
            </div>
          </div>
        </div>
        <div class="sub-panel">
          <h3>决策简报</h3>
          <p v-if="briefLoading" class="empty-state">正在生成决策简报...</p>
          <div v-else-if="brief" class="stack-list">
            <div class="info-card compact">
              <strong>{{ brief.verdict }}</strong>
              <p class="muted">{{ brief.summary }}</p>
            </div>
            <div class="info-card compact">
              <strong>关键判断</strong>
              <p class="muted">{{ brief.key_judgements.join('；') }}</p>
            </div>
            <div class="info-card compact">
              <strong>证据摘要</strong>
              <p class="muted">{{ brief.evidence_highlights.join('；') || '暂无' }}</p>
            </div>
          </div>
        </div>
        <div class="sub-panel">
          <h3>风险预测</h3>
          <p v-if="riskLoading" class="empty-state">正在生成风险预测...</p>
          <div v-else-if="risk" class="stack-list">
            <div class="info-card compact">
              <div class="trace-title-row">
                <strong>{{ risk.risk_level }}风险</strong>
                <span class="badge-subtle">{{ risk.risk_score }} 分</span>
              </div>
              <p class="muted">{{ risk.summary }}</p>
            </div>
            <div class="risk-score-grid">
              <div class="info-card compact">
                <strong>规则引擎分值</strong>
                <p class="metric-inline">{{ risk.heuristic_score.toFixed(1) }}</p>
              </div>
              <div class="info-card compact" v-if="risk.model_prediction">
                <strong>模型高风险概率</strong>
                <p class="metric-inline">{{ formatPercent(risk.model_prediction.high_risk_probability) }}</p>
              </div>
            </div>
            <div class="info-card compact" v-if="risk.model_prediction">
              <div class="trace-title-row">
                <strong>AI 风险模型</strong>
                <span class="badge-subtle">{{ risk.model_prediction.model_summary.model_ready ? 'Ready' : 'Pending' }}</span>
              </div>
              <p class="muted">
                训练样本 {{ risk.model_prediction.model_summary.sample_count }} 条，
                正样本 {{ risk.model_prediction.model_summary.positive_samples }} 条，
                ROC AUC {{ formatMetric(risk.model_prediction.model_summary.metrics.roc_auc) }}。
              </p>
              <div class="stack-list" v-if="risk.model_prediction.top_contributions.length">
                <div v-for="item in risk.model_prediction.top_contributions" :key="item.feature" class="factor-row">
                  <strong>{{ formatFeatureLabel(item.feature) }}</strong>
                  <span :class="item.direction === 'risk_up' ? 'tag-risk' : 'tag-safe'">
                    {{ item.direction === 'risk_up' ? '抬升风险' : '缓释风险' }} {{ item.contribution.toFixed(3) }}
                  </span>
                </div>
              </div>
            </div>
            <div class="info-card compact">
              <strong>风险驱动</strong>
              <p class="muted">{{ risk.drivers.join('；') }}</p>
            </div>
            <div class="info-card compact">
              <strong>监测指标</strong>
              <p class="muted">{{ risk.monitoring_items.join('；') }}</p>
            </div>
          </div>
        </div>
      </div>
    </PagePanel>

    <PagePanel title="Agent 问答与证据" eyebrow="Agent" description="面向真实数据的诊断问答，保留执行轨迹和命中证据。">
      <div class="button-row">
        <input v-model="question" class="text-input flex-grow" placeholder="例如：结合行业研报看迈瑞医疗的机会和风险" />
        <button class="button-primary" @click="runAgent">提交问题</button>
      </div>
      <div class="panel-split two-cols">
        <div class="sub-panel">
          <h3>问答结果</h3>
          <p v-if="agentLoading" class="empty-state">正在分析...</p>
          <div v-else-if="agentResult" class="stack-list">
            <div class="info-card compact">
              <strong>{{ agentResult.title }}</strong>
              <p class="muted">{{ agentResult.summary }}</p>
            </div>
            <div class="info-card compact" v-if="agentResult.highlights.length">
              <strong>关键结论</strong>
              <p class="muted">{{ agentResult.highlights.join('；') }}</p>
            </div>
          </div>
        </div>
        <div class="sub-panel">
          <h3>执行轨迹</h3>
          <TracePanel :trace="agentResult?.trace" />
        </div>
      </div>
      <div class="sub-panel">
        <h3>语义证据</h3>
        <EvidenceList :items="brief?.evidence.semantic_stock_reports || []" />
      </div>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import { api } from '../api/client';
import type { AgentResponse, CompanyReportResponse, DecisionBriefResponse, RiskForecastResponse } from '../api/types';
import EvidenceList from '../components/EvidenceList.vue';
import PagePanel from '../components/PagePanel.vue';
import TracePanel from '../components/TracePanel.vue';
import { useDashboardStore } from '../stores/dashboard';

const FEATURE_LABELS: Record<string, string> = {
  revenue_million: '营收规模',
  net_profit_million: '净利润规模',
  gross_margin_pct: '毛利率',
  net_margin_pct: '净利率',
  rd_ratio_pct: '研发强度',
  debt_ratio_pct: '资产负债率',
  current_ratio: '流动比率',
  cash_to_short_debt: '现金短债比',
  inventory_turnover: '存货周转率',
  receivable_turnover: '应收周转率',
  operating_cashflow_million: '经营现金流',
  roe_pct: 'ROE',
  revenue_yoy_pct: '营收同比',
  profit_yoy_pct: '利润同比',
  cashflow_yoy_change_million: '现金流同比变化',
  debt_ratio_change_pct: '负债率变化',
  current_ratio_change: '流动比率变化',
};

const props = defineProps<{ companyCode?: string }>();
const route = useRoute();
const store = useDashboardStore();
const selectedCode = ref(props.companyCode || '');
const report = ref<CompanyReportResponse | null>(null);
const brief = ref<DecisionBriefResponse | null>(null);
const risk = ref<RiskForecastResponse | null>(null);
const agentResult = ref<AgentResponse | null>(null);
const reportLoading = ref(false);
const briefLoading = ref(false);
const riskLoading = ref(false);
const agentLoading = ref(false);
const question = ref('结合行业研报看企业的机会和风险');

const targets = computed(() => store.targets);

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
  reportLoading.value = briefLoading.value = riskLoading.value = true;
  try {
    const [reportResult, briefResult, riskResult] = await Promise.all([
      api.getCompanyReport(selectedCode.value),
      api.getDecisionBrief(selectedCode.value, `结合行业研报看${currentCompanyName()}的机会和风险`),
      api.getRiskForecast(selectedCode.value),
    ]);
    report.value = reportResult;
    brief.value = briefResult;
    risk.value = riskResult;
    question.value = `结合行业研报看${currentCompanyName()}的机会和风险`;
  } finally {
    reportLoading.value = briefLoading.value = riskLoading.value = false;
  }
}

function currentCompanyName() {
  return targets.value.find((item) => item.company_code === selectedCode.value)?.company_name || '该企业';
}

function formatPercent(value: number | null | undefined) {
  return value == null ? '暂无' : `${(value * 100).toFixed(1)}%`;
}

function formatMetric(value: number | null | undefined) {
  return value == null ? '暂无' : value.toFixed(3);
}

function formatFeatureLabel(feature: string) {
  return FEATURE_LABELS[feature] || feature;
}

async function runAgent() {
  agentLoading.value = true;
  try {
    agentResult.value = await api.queryAgent(question.value || `分析${currentCompanyName()}`);
  } finally {
    agentLoading.value = false;
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

onMounted(async () => {
  await ensureTargets();
  if (selectedCode.value) {
    await loadAll();
  }
});
</script>
