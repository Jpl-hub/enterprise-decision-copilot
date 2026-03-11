<template>
  <div class="page-stack overview-page refined-overview unified-overview">
    <section class="command-stage unified-command-stage">
      <div class="command-stage-main">
        <div>
          <p class="section-tag">Agent Command</p>
          <h2>围绕一家企业，连续完成提问、判断和追问。</h2>
        </div>
        <div class="command-bar">
          <select v-model="selectedCode" class="select-input hero-select">
            <option v-for="item in store.targets" :key="item.company_code" :value="item.company_code">{{ item.company_name }}</option>
          </select>
          <RouterLink :to="selectedCode ? `/workbench/${selectedCode}` : '/workbench'" class="button-ghost hero-jump-button">查看企业详情</RouterLink>
        </div>
        <AgentWorkspacePanel
          :company-code="currentCompany()?.company_code"
          :company-name="currentCompany()?.company_name"
          :seed-question="seedQuestion"
          title="主分析区"
          eyebrow="Start Analysis"
          placeholder="直接输入经营、风险、竞争或行业问题"
        />
      </div>

      <div class="command-stage-side">
        <div class="agent-live-card">
          <div class="trace-title-row">
            <strong>当前对象</strong>
            <span class="badge-subtle" v-if="currentCompany()">{{ formatIndustry(currentCompany()?.industry) }}</span>
          </div>
          <div v-if="currentCompany()" class="stack-list">
            <div class="answer-hero-card">
              <strong>{{ currentCompany()?.company_name }}</strong>
              <p>{{ currentCompany()?.exchange }} · {{ formatIndustry(currentCompany()?.segment || currentCompany()?.industry) }}</p>
            </div>
            <RouterLink :to="selectedCode ? `/workbench/${selectedCode}` : '/workbench'" class="button-primary">查看结构化分析</RouterLink>
          </div>
        </div>

        <div class="mini-thread-card">
          <div class="trace-title-row">
            <strong>数据状态</strong>
            <RouterLink to="/quality">查看底座</RouterLink>
          </div>
          <div class="signal-stack-compact">
            <div class="signal-inline-item">
              <span>财报覆盖</span>
              <strong>{{ officialCoverageText }}</strong>
            </div>
            <div class="signal-inline-item">
              <span>图表抽取</span>
              <strong>{{ multimodalCoverageText }}</strong>
            </div>
            <div class="signal-inline-item">
              <span>待复核</span>
              <strong>{{ pendingReviewText }}</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink } from 'vue-router';

import { api } from '../api/client';
import type { QualitySummaryResponse } from '../api/types';
import AgentWorkspacePanel from '../components/AgentWorkspacePanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';
import { useDashboardStore } from '../stores/dashboard';

const store = useDashboardStore();
const agentStore = useAgentThreadStore();
const qualitySummary = ref<QualitySummaryResponse | null>(null);
const selectedCode = ref('');

const officialCoverageText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${qualitySummary.value.official_report_downloaded_slots} / ${qualitySummary.value.official_report_expected_slots}`;
});
const multimodalCoverageText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${Math.round((qualitySummary.value.multimodal_extract_coverage_ratio || 0) * 100)}%`;
});
const pendingReviewText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${qualitySummary.value.pending_review_count} 条`;
});
const seedQuestion = computed(() => {
  const company = currentCompany();
  return company ? `${company.company_name}当前最值得关注的经营问题是什么？` : '当前最值得关注的经营问题是什么？';
});

function currentCompany() {
  return store.targets.find((item) => item.company_code === selectedCode.value) || null;
}

function formatIndustry(value?: string | null) {
  if (!value) return '未分类';
  return value.replace('Ⅱ', '').replace('I', '').replace('Ⅲ', '').trim();
}

watch(selectedCode, (value) => {
  const company = store.targets.find((item) => item.company_code === value);
  if (company) {
    agentStore.setFocus(company.company_code, company.company_name);
    if (!agentStore.threadId) {
      agentStore.resetThread(company.company_code, company.company_name);
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
    }
  }
  qualitySummary.value = await api.getQualitySummary();
});
</script>
