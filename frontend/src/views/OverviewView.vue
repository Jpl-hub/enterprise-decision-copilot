<template>
  <div class="page-stack overview-page refined-overview">
    <section class="command-stage">
      <div class="command-stage-main">
        <div>
          <p class="section-tag">Agent Command</p>
          <h2>先选企业，再问一个经营问题。</h2>
        </div>
        <div class="command-bar">
          <select v-model="selectedCode" class="select-input hero-select">
            <option v-for="item in store.targets" :key="item.company_code" :value="item.company_code">{{ item.company_name }}</option>
          </select>
          <input
            v-model="question"
            class="text-input hero-input"
            placeholder="例如：未来两年的主要风险和机会是什么？"
            @keydown.enter="runAgent"
          />
          <button class="button-primary hero-button" @click="runAgent" :disabled="agentStore.loading">开始分析</button>
        </div>
        <div class="prompt-card-grid">
          <button v-for="prompt in quickPrompts" :key="prompt" class="prompt-card" @click="applyPrompt(prompt)">
            <strong>{{ prompt }}</strong>
          </button>
        </div>
        <div class="entry-grid compact-entry-grid">
          <RouterLink :to="selectedCode ? `/workbench/${selectedCode}` : '/workbench'" class="entry-card">
            <span>单家公司</span>
            <strong>进入企业分析台</strong>
          </RouterLink>
          <RouterLink to="/compare" class="entry-card">
            <span>多家公司</span>
            <strong>进入企业对比</strong>
          </RouterLink>
          <RouterLink to="/quality" class="entry-card">
            <span>数据底座</span>
            <strong>查看可信度</strong>
          </RouterLink>
        </div>
      </div>

      <div class="command-stage-side">
        <div class="agent-live-card">
          <div class="trace-title-row">
            <strong>Agent 当前回答</strong>
            <span class="badge-subtle" v-if="agentStore.focusCompanyName">{{ agentStore.focusCompanyName }}</span>
          </div>
          <div v-if="agentStore.loading" class="empty-state">正在生成判断...</div>
          <div v-else-if="agentStore.latest" class="stack-list">
            <div class="answer-hero-card">
              <strong>{{ agentStore.latest.title }}</strong>
              <p>{{ agentStore.latest.summary }}</p>
            </div>
            <div v-for="item in agentStore.latest.highlights.slice(0, 3)" :key="item" class="answer-line-card">
              <p>{{ item }}</p>
            </div>
            <div class="next-action-strip" v-if="agentStore.latest.suggested_questions?.length">
              <button
                v-for="item in agentStore.latest.suggested_questions.slice(0, 3)"
                :key="item"
                class="button-ghost chip-button"
                @click="applyPrompt(item)"
              >
                {{ item }}
              </button>
            </div>
          </div>
          <div v-else class="starter-stack">
            <div class="starter-step">
              <span>1</span>
              <p>选一家企业</p>
            </div>
            <div class="starter-step">
              <span>2</span>
              <p>问经营、风险或竞争问题</p>
            </div>
            <div class="starter-step">
              <span>3</span>
              <p>继续追问，直到形成动作判断</p>
            </div>
          </div>
        </div>

        <div class="mini-thread-card">
          <div class="trace-title-row">
            <strong>最近对话</strong>
            <RouterLink to="/threads">全部记录</RouterLink>
          </div>
          <AgentThreadPanel :messages="agentStore.messages.slice(-4)" />
        </div>
      </div>
    </section>

    <section class="signal-band">
      <div class="signal-box">
        <span>财报覆盖</span>
        <strong>{{ officialCoverageText }}</strong>
        <div class="signal-meter"><div class="signal-meter-fill" :style="{ width: `${officialCoverageRatio * 100}%` }"></div></div>
      </div>
      <div class="signal-box">
        <span>图表抽取</span>
        <strong>{{ multimodalCoverageText }}</strong>
        <div class="signal-meter"><div class="signal-meter-fill accent" :style="{ width: `${multimodalCoverageRatio * 100}%` }"></div></div>
      </div>
      <div class="signal-box">
        <span>研报接入</span>
        <strong>{{ researchCountText }}</strong>
        <div class="signal-meter"><div class="signal-meter-fill dark" :style="{ width: researchMeterWidth }"></div></div>
      </div>
      <div class="signal-box warning">
        <span>待复核</span>
        <strong>{{ pendingReviewText }}</strong>
        <div class="signal-meter"><div class="signal-meter-fill warning" :style="{ width: pendingReviewWidth }"></div></div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink } from 'vue-router';

import { api } from '../api/client';
import type { QualitySummaryResponse } from '../api/types';
import AgentThreadPanel from '../components/AgentThreadPanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';
import { useDashboardStore } from '../stores/dashboard';

const store = useDashboardStore();
const agentStore = useAgentThreadStore();
const qualitySummary = ref<QualitySummaryResponse | null>(null);
const selectedCode = ref('');
const question = ref('当前最值得关注的经营问题是什么？');

const quickPrompts = [
  '当前最值得关注的经营问题是什么？',
  '未来两年的主要风险和机会是什么？',
  '把风险拆成财务、经营、行业三层',
];

const officialCoverageRatio = computed(() => qualitySummary.value?.official_report_coverage_ratio ?? 0);
const multimodalCoverageRatio = computed(() => qualitySummary.value?.multimodal_extract_coverage_ratio ?? 0);
const officialCoverageText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${qualitySummary.value.official_report_downloaded_slots} / ${qualitySummary.value.official_report_expected_slots}`;
});
const multimodalCoverageText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${Math.round((qualitySummary.value.multimodal_extract_coverage_ratio || 0) * 100)}%`;
});
const researchCountText = computed(() => {
  if (!store.payload?.metrics) return '加载中';
  return String(store.payload.metrics.research_report_count + store.payload.metrics.industry_report_count);
});
const researchMeterWidth = computed(() => {
  const count = (store.payload?.metrics?.research_report_count || 0) + (store.payload?.metrics?.industry_report_count || 0);
  return `${Math.min(100, Math.max(18, count / 4))}%`;
});
const pendingReviewText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${qualitySummary.value.pending_review_count} 条`;
});
const pendingReviewWidth = computed(() => {
  const pending = qualitySummary.value?.pending_review_count || 0;
  return `${Math.min(100, Math.max(10, pending * 10))}%`;
});

function currentCompany() {
  return store.targets.find((item) => item.company_code === selectedCode.value) || null;
}

function normalizeQuestion(prompt: string) {
  const companyName = currentCompany()?.company_name || '这家公司';
  return prompt.replace(/这家?公司/g, companyName);
}

function applyPrompt(prompt: string) {
  question.value = normalizeQuestion(prompt);
  void runAgent();
}

async function runAgent() {
  const company = currentCompany();
  if (!question.value.trim()) return;
  await agentStore.ask(question.value.trim(), {
    companyCode: company?.company_code,
    companyName: company?.company_name,
  });
}

watch(selectedCode, (value) => {
  const company = store.targets.find((item) => item.company_code === value);
  if (company) {
    agentStore.setFocus(company.company_code, company.company_name);
    if (!question.value.includes(company.company_name)) {
      question.value = `${company.company_name}${quickPrompts[0]}`;
    }
  }
});

onMounted(async () => {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  if (!selectedCode.value && store.targets.length) {
    selectedCode.value = store.targets[0].company_code;
    const company = currentCompany();
    if (company) {
      agentStore.resetThread(company.company_code, company.company_name);
      question.value = `${company.company_name}${quickPrompts[0]}`;
    }
  }
  qualitySummary.value = await api.getQualitySummary();
});
</script>
