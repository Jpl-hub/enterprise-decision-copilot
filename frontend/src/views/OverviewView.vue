<template>
  <div class="page-stack overview-page clean-overview">
    <section class="analysis-stage-card">
      <div class="analysis-stage-topbar">
        <label class="console-field analysis-company-picker">
          <span>分析企业</span>
          <select v-model="selectedCode" class="select-input hero-select">
            <option v-for="item in store.targets" :key="item.company_code" :value="String(item.company_code)">{{ item.company_name }}</option>
          </select>
        </label>

        <div class="analysis-focus-inline" v-if="currentCompany">
          <div class="analysis-focus-identity">
            <strong>{{ currentCompany.company_name }}</strong>
            <span>{{ formatExchange(currentCompany.exchange) }}</span>
          </div>
          <span class="analysis-focus-pill">{{ formatIndustry(currentCompany.industry) }}</span>
          <span class="analysis-focus-pill">{{ currentTaskLabel }}</span>
          <span class="analysis-focus-pill">{{ currentRiskText }}</span>
          <span class="analysis-focus-pill">{{ currentScoreText }}</span>
        </div>

        <RouterLink :to="selectedCode ? `/workbench/${selectedCode}` : '/workbench'" class="button-ghost console-link-button">企业详情</RouterLink>
      </div>

      <AgentWorkspacePanel
        :company-code="currentCompany?.company_code ? String(currentCompany.company_code) : null"
        :company-name="currentCompany?.company_name"
        :seed-question="seedQuestion"
        title=""
        eyebrow=""
        placeholder="直接提问，例如：这家公司最值得盯的经营问题是什么？"
      />
    </section>

    <section class="overview-lower-grid compact-overview-grid">
      <article class="support-panel compact-plan-panel">
        <div class="panel-header-row compact-panel-header">
          <div>
            <p class="section-tag">继续分析</p>
            <h3>你可以继续这样问</h3>
          </div>
        </div>

        <div class="plan-item-list compact-plan-list">
          <button v-for="item in projectPlanItems" :key="item.title" class="plan-item-card plan-item-button" @click="applyFollowupPrompt(item.prompt)">
            <strong>{{ item.title }}</strong>
            <p>{{ item.body }}</p>
          </button>
        </div>
      </article>

      <article class="support-panel compact-support-panel">
        <div class="panel-header-row compact-panel-header">
          <div>
            <p class="section-tag">企业雷达</p>
            <h3>重点企业</h3>
          </div>
        </div>

        <div class="radar-list compact-radar-list" v-if="rankingRows.length">
          <div v-for="item in rankingRows" :key="item.company_code" class="radar-item compact-radar-item">
            <div class="radar-head">
              <strong>{{ item.company_name }}</strong>
              <span>{{ scoreText(item.total_score) }}</span>
            </div>
            <div class="bar-track"><div class="bar-fill" :style="{ width: `${Math.max(18, Number(item.total_score) || 0)}%` }"></div></div>
            <div class="radar-meta">
              <span>{{ item.risk_level }}风险</span>
              <button class="text-link-button" @click="focusCompany(item.company_code)">带入分析</button>
            </div>
          </div>
        </div>
      </article>
    </section>

    <section class="analysis-support-strip">
      <div class="metric-mini-card support-strip-card">
        <span>风险模型 AUC</span>
        <strong>{{ riskAucText }}</strong>
      </div>
      <div class="metric-mini-card support-strip-card">
        <span>多模态覆盖率</span>
        <strong>{{ multimodalCoverageText }}</strong>
      </div>
      <div class="support-note-card">
        <strong>证据链说明</strong>
        <p>当前分析会优先结合财报、研报和宏观数据给出结论，详细来源留在线程结果里展开。</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink } from 'vue-router';

import { api } from '../api/client';
import type { QualitySummaryResponse, RiskModelSummaryResponse } from '../api/types';
import AgentWorkspacePanel from '../components/AgentWorkspacePanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';
import { useDashboardStore } from '../stores/dashboard';

interface RankingRow {
  company_code: string;
  company_name: string;
  total_score: number;
  risk_level: string;
}

const taskModeLabels: Record<string, string> = {
  company_diagnosis: '企业诊断',
  company_risk_forecast: '风险预警',
  company_decision_brief: '决策建议',
  industry_trend: '行业趋势',
  data_quality: '数据底座',
};

const exchangeLabels: Record<string, string> = {
  SSE: '上交所',
  SZSE: '深交所',
  BSE: '北交所',
};

const store = useDashboardStore();
const agentStore = useAgentThreadStore();
const selectedCode = ref('');
const qualitySummary = ref<QualitySummaryResponse | null>(null);
const riskModelSummary = ref<RiskModelSummaryResponse | null>(null);

const rankingRows = computed<RankingRow[]>(() => ((store.payload?.ranking || []) as unknown as RankingRow[]).slice(0, 5));
const currentCompany = computed(() => store.targets.find((item) => String(item.company_code) === selectedCode.value) || null);
const currentRanking = computed<RankingRow | null>(() => {
  return ((store.payload?.ranking || []) as unknown as RankingRow[]).find((item) => String(item.company_code) === selectedCode.value) || null;
});
const currentTaskLabel = computed(() => taskModeLabels[agentStore.taskMode || 'company_diagnosis'] || '企业诊断');
const currentRiskText = computed(() => currentRanking.value ? `${currentRanking.value.risk_level}风险` : '待分析');
const currentScoreText = computed(() => currentRanking.value ? scoreText(currentRanking.value.total_score) : '待分析');
const companyName = computed(() => currentCompany.value?.company_name || '这家公司');
const seedQuestion = computed(() => {
  return currentCompany.value ? `${currentCompany.value.company_name}当前最值得关注的经营问题是什么？` : '当前最值得关注的经营问题是什么？';
});
const projectPlanItems = computed(() => [
  {
    title: '先看经营问题',
    body: '直接问最值得关注的经营问题、增长压力、盈利质量或现金流变化。',
    prompt: `${companyName.value}当前最值得关注的经营问题是什么？`,
  },
  {
    title: '再拆风险层次',
    body: '继续追问财务、经营、行业三层风险，系统会给出监测项。',
    prompt: `把${companyName.value}的风险拆成财务、经营、行业三层`,
  },
  {
    title: '最后要动作建议',
    body: '如果已经有结论，再问动作建议、管理层优先级或下一步判断。',
    prompt: `给出${companyName.value}当前的经营判断和动作建议`,
  },
]);
const riskAucText = computed(() => riskModelSummary.value?.metrics?.roc_auc?.toFixed(3) || '暂无');
const multimodalCoverageText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${Math.round((qualitySummary.value.multimodal_extract_coverage_ratio || 0) * 100)}%`;
});

function formatIndustry(value?: string | null) {
  if (!value) return '未分类';
  return value.replace('Ⅱ', '').replace('I', '').replace('Ⅲ', '').trim();
}

function formatExchange(value?: string | null) {
  return exchangeLabels[String(value || '').toUpperCase()] || String(value || '未标注');
}

function scoreText(value: unknown) {
  const num = typeof value === 'number' ? value : Number(value || 0);
  return `${num.toFixed(1)} 分`;
}

function focusCompany(companyCode: string) {
  selectedCode.value = String(companyCode);
}

async function applyFollowupPrompt(prompt: string) {
  const company = currentCompany.value;
  if (!company) return;
  await agentStore.ask(prompt, {
    companyCode: String(company.company_code),
    companyName: company.company_name,
  });
}

watch(selectedCode, (value, previous) => {
  const company = store.targets.find((item) => String(item.company_code) === value);
  if (!company) return;
  agentStore.setFocus(String(company.company_code), company.company_name);
  if (value !== previous) {
    agentStore.resetThread(String(company.company_code), company.company_name);
  }
});

onMounted(async () => {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  if (!selectedCode.value && store.targets.length) {
    selectedCode.value = String(store.targets[0].company_code);
    const company = currentCompany.value;
    if (company) {
      agentStore.resetThread(String(company.company_code), company.company_name);
    }
  }
  const [quality, riskSummary] = await Promise.all([
    api.getQualitySummary(),
    api.getRiskModelSummary(),
  ]);
  qualitySummary.value = quality;
  riskModelSummary.value = riskSummary;
});
</script>
