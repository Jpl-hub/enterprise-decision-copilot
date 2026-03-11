<template>
  <div class="page-stack workbench-page">
    <PagePanel title="企业分析主台" eyebrow="Enterprise Analysis" description="围绕一家公司完成结论、证据、风险和追问，不让用户在多个页面之间来回拼接。">
      <template #actions>
        <div class="toolbar-cluster">
          <select v-model="selectedCode" class="select-input toolbar-select">
            <option v-for="item in targets" :key="item.company_code" :value="item.company_code">{{ item.company_name }}</option>
          </select>
          <button class="button-primary" @click="loadAll">刷新分析</button>
        </div>
      </template>

      <div class="analysis-hero" v-if="report">
        <div class="analysis-hero-main">
          <p class="section-tag">Current Target</p>
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

      <div class="analysis-grid two-main-one-side">
        <div class="analysis-main-stack">
          <div class="sub-panel">
            <div class="sub-panel-header">
              <h3>决策结论</h3>
              <span class="badge-subtle">Agent-ready</span>
            </div>
            <div v-if="briefLoading" class="empty-state">正在生成决策简报...</div>
            <div v-else-if="brief" class="stack-list">
              <div class="info-card compact emphasis-card">
                <strong>{{ brief.verdict }}</strong>
                <p class="muted">{{ brief.summary }}</p>
              </div>
              <div class="info-card compact">
                <strong>关键判断</strong>
                <p class="muted">{{ brief.key_judgements.join('；') }}</p>
              </div>
              <div class="info-card compact">
                <strong>建议动作</strong>
                <p class="muted">{{ brief.action_recommendations.join('；') }}</p>
              </div>
              <div class="info-card compact" v-if="brief.evidence_highlights.length">
                <strong>证据摘要</strong>
                <p class="muted">{{ brief.evidence_highlights.join('；') }}</p>
              </div>
            </div>
          </div>

          <div class="sub-panel">
            <div class="sub-panel-header">
              <h3>经营分析</h3>
              <RouterLink :to="`/competition/${selectedCode}`">导出分析材料</RouterLink>
            </div>
            <div v-if="reportLoading" class="empty-state">正在生成综合报告...</div>
            <div v-else-if="report" class="stack-list">
              <div v-for="section in report.sections" :key="section.title" class="info-card compact section-card">
                <strong>{{ section.title }}</strong>
                <p class="muted">{{ section.content }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="analysis-side-stack">
          <div class="sub-panel">
            <h3>风险画像</h3>
            <div v-if="riskLoading" class="empty-state">正在生成风险预测...</div>
            <div v-else-if="risk" class="stack-list">
              <div class="info-card compact">
                <strong>{{ risk.summary }}</strong>
                <p class="muted">规则引擎 {{ risk.heuristic_score.toFixed(1) }} 分</p>
              </div>
              <div class="info-card compact" v-if="risk.model_prediction">
                <strong>AI 风险模型</strong>
                <p class="muted">
                  高风险概率 {{ formatPercent(risk.model_prediction.high_risk_probability) }} ·
                  AUC {{ formatMetric(risk.model_prediction.model_summary.metrics.roc_auc) }}
                </p>
              </div>
              <div class="info-card compact">
                <strong>主要驱动</strong>
                <p class="muted">{{ risk.drivers.join('；') }}</p>
              </div>
              <div class="info-card compact">
                <strong>监测项</strong>
                <p class="muted">{{ risk.monitoring_items.join('；') }}</p>
              </div>
            </div>
          </div>

          <div class="sub-panel">
            <h3>语义证据</h3>
            <EvidenceList :items="brief?.evidence.semantic_stock_reports || []" />
          </div>
        </div>
      </div>
    </PagePanel>

    <PagePanel title="Agent 深问" eyebrow="Follow-up" description="你可以继续追问，系统保留工具轨迹和回答证据。">
      <div class="hero-command">
        <input v-model="question" class="text-input hero-input" placeholder="继续追问，例如：把风险拆成财务、经营、行业三层" @keydown.enter="runAgent" />
        <button class="button-primary hero-button" @click="runAgent">继续追问</button>
      </div>
      <div class="panel-split two-cols">
        <div class="sub-panel">
          <h3>Agent 输出</h3>
          <p v-if="agentLoading" class="empty-state">正在分析...</p>
          <div v-else-if="agentResult" class="stack-list">
            <div class="info-card compact emphasis-card">
              <strong>{{ agentResult.title }}</strong>
              <p class="muted">{{ agentResult.summary }}</p>
            </div>
            <div v-for="item in agentResult.highlights" :key="item" class="info-card compact">
              <p class="muted">{{ item }}</p>
            </div>
          </div>
        </div>
        <div class="sub-panel">
          <h3>工具轨迹</h3>
          <TracePanel :trace="agentResult?.trace" />
        </div>
      </div>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, RouterLink } from 'vue-router';

import { api } from '../api/client';
import type { AgentResponse, CompanyReportResponse, DecisionBriefResponse, RiskForecastResponse } from '../api/types';
import EvidenceList from '../components/EvidenceList.vue';
import PagePanel from '../components/PagePanel.vue';
import TracePanel from '../components/TracePanel.vue';
import { useDashboardStore } from '../stores/dashboard';

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
const question = ref('把这家企业的风险拆成财务、经营、行业三层并给出动作建议');

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
  reportLoading.value = true;
  briefLoading.value = true;
  riskLoading.value = true;
  try {
    const companyName = currentCompanyName();
    const [reportResult, briefResult, riskResult] = await Promise.all([
      api.getCompanyReport(selectedCode.value),
      api.getDecisionBrief(selectedCode.value, `结合财报、研报和风险模型，给出${companyName}的经营判断和动作建议`),
      api.getRiskForecast(selectedCode.value),
    ]);
    report.value = reportResult;
    brief.value = briefResult;
    risk.value = riskResult;
    question.value = `把${companyName}的风险拆成财务、经营、行业三层并给出动作建议`;
    await runAgent();
  } finally {
    reportLoading.value = false;
    briefLoading.value = false;
    riskLoading.value = false;
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

async function runAgent() {
  if (!question.value.trim()) return;
  agentLoading.value = true;
  try {
    agentResult.value = await api.queryAgent(question.value.trim());
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
