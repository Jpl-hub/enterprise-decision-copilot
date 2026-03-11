<template>
  <div class="page-stack overview-page refined-overview unified-overview advanced-overview">
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
              <span>待处理问题</span>
              <strong>{{ pendingIssueText }}</strong>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="mission-deck">
      <button class="mission-card" @click="applyMission('risk')">
        <span>风险预警</span>
        <strong>拆解财务、经营、行业三层风险</strong>
        <p>适合先判断该防什么、先盯什么。</p>
      </button>
      <button class="mission-card" @click="applyMission('compare')">
        <span>同业对比</span>
        <strong>判断谁更值得重点跟踪</strong>
        <p>直接切到企业对比的主结论视角。</p>
      </button>
      <button class="mission-card" @click="applyMission('growth')">
        <span>增长机会</span>
        <strong>找未来两年的主要机会与变量</strong>
        <p>适合管理层讨论扩张、投入与节奏。</p>
      </button>
    </section>

    <section class="cockpit-grid">
      <div class="cockpit-panel radar-panel">
        <div class="panel-header-row">
          <div>
            <p class="section-tag">Decision Radar</p>
            <h2>关注名单</h2>
          </div>
          <span class="badge-subtle">实时筛选</span>
        </div>
        <div class="radar-list" v-if="rankingRows.length">
          <div v-for="item in rankingRows" :key="item.company_code" class="radar-item">
            <div class="radar-head">
              <strong>{{ item.company_name }}</strong>
              <span>{{ scoreText(item.total_score) }}</span>
            </div>
            <div class="bar-track"><div class="bar-fill" :style="{ width: `${Math.max(18, Number(item.total_score) || 0)}%` }"></div></div>
            <div class="radar-meta">
              <span>风险 {{ item.risk_level }}</span>
              <RouterLink :to="`/workbench/${item.company_code}`">进入分析</RouterLink>
            </div>
          </div>
        </div>
      </div>

      <div class="cockpit-panel queue-panel">
        <div class="panel-header-row">
          <div>
            <p class="section-tag">Watch Queue</p>
            <h2>高优先级观察</h2>
          </div>
          <span class="badge-subtle">先处理这些</span>
        </div>
        <div class="queue-list" v-if="watchlistRows.length">
          <div v-for="item in watchlistRows" :key="item.company_code" class="queue-card">
            <div class="trace-title-row">
              <strong>{{ item.company_name }}</strong>
              <span>{{ item.risk_level }}</span>
            </div>
            <p>{{ riskFlagText(item.risk_flags) }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="ai-stack-board" v-if="visibleEngines.length">
      <div v-for="engine in visibleEngines" :key="engine.engine_id" class="stack-engine-card">
        <div class="trace-title-row">
          <strong>{{ engine.name }}</strong>
          <span class="badge-subtle">{{ engine.category }}</span>
        </div>
        <p>{{ engine.role }}</p>
        <div class="stack-chip-row">
          <span v-for="item in engine.primary_outputs.slice(0, 3)" :key="item" class="selected-pill">{{ item }}</span>
        </div>
      </div>
    </section>

    <section class="ai-deck-grid">
      <div class="ai-engine-card primary-engine-card">
        <div class="trace-title-row">
          <strong>决策大模型</strong>
          <span class="badge-subtle">Agent 编排</span>
        </div>
        <div class="engine-ring" :style="ringStyle(0.82, '#153e75', '#dbe9f7')">
          <div>
            <span>连续分析度</span>
            <strong>82%</strong>
          </div>
        </div>
        <p>主分析区会自动执行：锁定对象、判断任务类型、选择分析路径、输出结果。</p>
      </div>

      <div class="ai-engine-card">
        <div class="trace-title-row">
          <strong>风险预测模型</strong>
          <span class="badge-subtle">Deep Learning / ML</span>
        </div>
        <div class="engine-ring" :style="ringStyle(riskAucRatio, '#d86137', '#f5e0d7')">
          <div>
            <span>AUC</span>
            <strong>{{ riskAucText }}</strong>
          </div>
        </div>
        <p>{{ riskModelText }}</p>
      </div>

      <div class="ai-engine-card">
        <div class="trace-title-row">
          <strong>多模态抽取</strong>
          <span class="badge-subtle">Vision + LLM</span>
        </div>
        <div class="engine-ring" :style="ringStyle(multimodalCoverageRatio, '#1f7a6b', '#d9efe9')">
          <div>
            <span>覆盖率</span>
            <strong>{{ multimodalCoverageText }}</strong>
          </div>
        </div>
        <p>{{ multimodalText }}</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

import { api } from '../api/client';
import type { AIEngineSummary, AIStackSummaryResponse, QualitySummaryResponse, RiskModelSummaryResponse } from '../api/types';

interface RankingRow {
  company_code: string;
  company_name: string;
  total_score: number;
  risk_level: string;
}

interface WatchRow {
  company_code: string;
  company_name: string;
  risk_level: string;
  risk_flags: string[];
}
import AgentWorkspacePanel from '../components/AgentWorkspacePanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';
import { useDashboardStore } from '../stores/dashboard';

const store = useDashboardStore();
const agentStore = useAgentThreadStore();
const router = useRouter();
const qualitySummary = ref<QualitySummaryResponse | null>(null);
const riskModelSummary = ref<RiskModelSummaryResponse | null>(null);
const aiStack = ref<AIStackSummaryResponse | null>(null);
const selectedCode = ref('');

const officialCoverageText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${qualitySummary.value.official_report_downloaded_slots} / ${qualitySummary.value.official_report_expected_slots}`;
});
const multimodalCoverageRatio = computed(() => qualitySummary.value?.multimodal_extract_coverage_ratio ?? 0);
const multimodalCoverageText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${Math.round((qualitySummary.value.multimodal_extract_coverage_ratio || 0) * 100)}%`;
});
const pendingIssueText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${qualitySummary.value.pending_review_count} 条`;
});
const seedQuestion = computed(() => {
  const company = currentCompany();
  return company ? `${company.company_name}当前最值得关注的经营问题是什么？` : '当前最值得关注的经营问题是什么？';
});
const rankingRows = computed<RankingRow[]>(() => ((store.payload?.ranking || []) as unknown as RankingRow[]).slice(0, 5));
const watchlistRows = computed<WatchRow[]>(() => ((store.payload?.watchlist || []) as unknown as WatchRow[]).slice(0, 4));
const riskAucRatio = computed(() => riskModelSummary.value?.metrics?.roc_auc ?? 0);
const riskAucText = computed(() => riskModelSummary.value?.metrics?.roc_auc?.toFixed(3) || '暂无');
const riskModelText = computed(() => {
  if (!riskModelSummary.value?.model_ready) return '风险模型尚未完成训练或尚未接入最新样本。';
  return `已接入 ${riskModelSummary.value.sample_count} 条样本，当前高风险识别以 ${riskModelSummary.value.model_type || '模型'} 为主。`;
});
const multimodalText = computed(() => {
  if (!qualitySummary.value) return '正在读取图表与表格抽取状态。';
  const backend = qualitySummary.value.multimodal_backends.join(' / ') || '多模态链路';
  return `${backend} 已补全平均 ${qualitySummary.value.multimodal_avg_filled_field_count.toFixed(1)} 个字段。`;
});

function currentCompany() {
  return store.targets.find((item) => item.company_code === selectedCode.value) || null;
}

function formatIndustry(value?: string | null) {
  if (!value) return '未分类';
  return value.replace('Ⅱ', '').replace('I', '').replace('Ⅲ', '').trim();
}

function scoreText(value: unknown) {
  const num = typeof value === 'number' ? value : Number(value || 0);
  return `${num.toFixed(1)} 分`;
}

function riskFlagText(value: unknown) {
  const flags = Array.isArray(value) ? value : [];
  return flags.length ? flags.join('；') : '当前没有高优先级异常信号。';
}

const visibleEngines = computed<AIEngineSummary[]>(() => (aiStack.value?.engines || []).slice(0, 4));

function ringStyle(value: number, color: string, base: string) {
  const angle = Math.max(0, Math.min(100, value * 100));
  return {
    background: `conic-gradient(${color} ${angle}%, ${base} ${angle}% 100%)`,
  };
}

async function applyMission(mode: 'risk' | 'compare' | 'growth') {
  const company = currentCompany();
  if (mode === 'compare') {
    await router.push({ name: 'compare' });
    return;
  }
  if (!company) return;
  const prompts = {
    risk: `把${company.company_name}的风险拆成财务、经营、行业三层并给出动作建议`,
    growth: `${company.company_name}未来两年的主要机会、变量和投入重点是什么？`,
  };
  agentStore.resetThread(company.company_code, company.company_name);
  await agentStore.ask(prompts[mode], {
    companyCode: company.company_code,
    companyName: company.company_name,
    taskMode: mode === 'risk' ? 'company_risk_forecast' : 'company_decision_brief',
  });
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
  const [quality, riskSummary, stack] = await Promise.all([
    api.getQualitySummary(),
    api.getRiskModelSummary(),
    api.getAIStack(),
  ]);
  qualitySummary.value = quality;
  riskModelSummary.value = riskSummary;
  aiStack.value = stack;
});
</script>
