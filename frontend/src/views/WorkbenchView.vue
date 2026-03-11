<template>
  <div class="page-stack workbench-page refined-workbench">
    <PagePanel title="企业分析台" eyebrow="Enterprise Analysis">
      <template #actions>
        <div class="toolbar-cluster">
          <select v-model="selectedCode" class="select-input toolbar-select">
            <option v-for="item in targets" :key="item.company_code" :value="item.company_code">{{ item.company_name }}</option>
          </select>
          <button class="button-primary" @click="loadAll">刷新</button>
        </div>
      </template>

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

      <div class="analysis-grid two-main-one-side">
        <div class="analysis-main-stack">
          <div class="sub-panel">
            <div class="sub-panel-header">
              <h3>当前判断</h3>
              <RouterLink :to="`/competition/${selectedCode}`">导出材料</RouterLink>
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
            <h3>风险画像</h3>
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
            </div>
          </div>

          <div class="sub-panel">
            <h3>证据资料</h3>
            <EvidenceList :items="brief?.evidence.semantic_stock_reports || []" />
          </div>
        </div>
      </div>
    </PagePanel>

    <PagePanel title="Agent 对话区" eyebrow="Agent Thread">
      <div class="agent-workspace-grid">
        <div class="sub-panel">
          <div class="hero-command compact-agent-command">
            <input v-model="question" class="text-input hero-input" placeholder="继续拆解这家企业的问题" @keydown.enter="runAgent" />
            <button class="button-primary hero-button" @click="runAgent" :disabled="agentStore.loading">发送</button>
          </div>
          <div class="quick-prompt-row left-align top-gap" v-if="agentStore.latest?.suggested_questions?.length">
            <button v-for="item in agentStore.latest.suggested_questions.slice(0, 4)" :key="item" class="button-ghost chip-button" @click="applySuggestedQuestion(item)">
              {{ item }}
            </button>
          </div>
          <div class="stack-list top-gap">
            <div v-if="agentStore.loading" class="empty-state">正在分析...</div>
            <template v-else-if="agentStore.latest">
              <div class="info-card compact emphasis-card">
                <strong>{{ agentStore.latest.title }}</strong>
                <p>{{ agentStore.latest.summary }}</p>
              </div>
              <div v-for="item in agentStore.latest.highlights" :key="item" class="info-card compact">
                <p>{{ item }}</p>
              </div>
            </template>
          </div>
        </div>

        <div class="sub-panel">
          <div class="sub-panel-header">
            <h3>本轮计划</h3>
            <button class="button-ghost" @click="resetThread">新建线程</button>
          </div>
          <TracePanel :trace="agentStore.latest?.plan" />
          <div class="top-gap">
            <AgentThreadPanel :messages="agentStore.messages" />
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
import type { CompanyReportResponse, DecisionBriefResponse, RiskForecastResponse } from '../api/types';
import AgentThreadPanel from '../components/AgentThreadPanel.vue';
import EvidenceList from '../components/EvidenceList.vue';
import PagePanel from '../components/PagePanel.vue';
import TracePanel from '../components/TracePanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';
import { useDashboardStore } from '../stores/dashboard';

const props = defineProps<{ companyCode?: string }>();
const route = useRoute();
const store = useDashboardStore();
const agentStore = useAgentThreadStore();
const selectedCode = ref(props.companyCode || '');
const report = ref<CompanyReportResponse | null>(null);
const brief = ref<DecisionBriefResponse | null>(null);
const risk = ref<RiskForecastResponse | null>(null);
const reportLoading = ref(false);
const briefLoading = ref(false);
const riskLoading = ref(false);
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
    agentStore.setFocus(selectedCode.value, companyName);
    const [reportResult, briefResult, riskResult] = await Promise.all([
      api.getCompanyReport(selectedCode.value),
      api.getDecisionBrief(selectedCode.value, `结合财报、研报和风险模型，给出${companyName}的经营判断和动作建议`),
      api.getRiskForecast(selectedCode.value),
    ]);
    report.value = reportResult;
    brief.value = briefResult;
    risk.value = riskResult;
    question.value = `把${companyName}的风险拆成财务、经营、行业三层并给出动作建议`;
    if (!agentStore.latest || agentStore.focusCompanyCode !== selectedCode.value) {
      agentStore.resetThread(selectedCode.value, companyName);
      await runAgent();
    }
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

function applySuggestedQuestion(text: string) {
  question.value = text;
  void runAgent();
}

function resetThread() {
  agentStore.resetThread(selectedCode.value, currentCompanyName());
}

async function runAgent() {
  if (!question.value.trim()) return;
  await agentStore.ask(question.value.trim(), {
    companyCode: selectedCode.value,
    companyName: currentCompanyName(),
  });
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
