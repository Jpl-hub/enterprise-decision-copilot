<template>
  <div class="page-stack overview-page refined-overview unified-overview advanced-overview">
    <section class="command-stage unified-command-stage">
      <div class="command-stage-main polished-command-stage-main">
        <div class="command-stage-intro">
          <p class="section-tag">开始分析</p>
          <h2>先选企业，再连续提问。</h2>
          <p class="hero-copy">经营、风险、机会、行业变化，都从这里开始。</p>
        </div>

        <div class="command-bar single-line-command-bar">
          <select v-model="selectedCode" class="select-input hero-select">
            <option v-for="item in store.targets" :key="item.company_code" :value="String(item.company_code)">{{ item.company_name }}</option>
          </select>
          <span class="selected-task-pill">{{ currentTaskLabel }}</span>
        </div>

        <AgentWorkspacePanel
          :company-code="currentCompany?.company_code ? String(currentCompany.company_code) : null"
          :company-name="currentCompany?.company_name"
          :seed-question="seedQuestion"
          title="主分析区"
          eyebrow="开始分析"
          placeholder="直接输入经营、风险、竞争或行业问题"
        />
      </div>

      <div class="command-stage-side refined-command-side">
        <div class="focus-summary-card">
          <div class="trace-title-row" v-if="currentCompany">
            <strong>{{ currentCompany.company_name }}</strong>
            <span class="badge-subtle market-chip">{{ formatExchange(currentCompany.exchange) }}</span>
          </div>
          <template v-if="currentCompany">
            <p class="focus-summary-line">{{ formatIndustry(currentCompany.segment || currentCompany.industry) }} · {{ formatIndustry(currentCompany.industry) }}</p>
            <div class="focus-metric-grid">
              <div class="focus-metric-card">
                <span>当前风险</span>
                <strong>{{ currentRiskText }}</strong>
              </div>
              <div class="focus-metric-card">
                <span>综合表现</span>
                <strong>{{ currentScoreText }}</strong>
              </div>
              <div class="focus-metric-card">
                <span>当前任务</span>
                <strong>{{ currentTaskLabel }}</strong>
              </div>
            </div>
            <div class="focus-note-card">
              <p>{{ focusSummaryText }}</p>
            </div>
            <RouterLink :to="selectedCode ? `/workbench/${selectedCode}` : '/workbench'" class="button-primary focus-detail-button">查看企业详情</RouterLink>
          </template>
        </div>

        <div class="focus-status-card">
          <div class="trace-title-row">
            <strong>当前可用资料</strong>
            <RouterLink to="/quality">查看底座</RouterLink>
          </div>
          <div class="focus-status-list">
            <div class="focus-status-item">
              <span>官方年报</span>
              <strong>{{ reportReadinessText }}</strong>
            </div>
            <div class="focus-status-item">
              <span>行业与研究资料</span>
              <strong>{{ researchReadinessText }}</strong>
            </div>
            <div class="focus-status-item">
              <span>图表补全</span>
              <strong>{{ multimodalCoverageText }}</strong>
            </div>
            <div class="focus-status-item">
              <span>数据提醒</span>
              <strong>{{ issueDigestText }}</strong>
            </div>
          </div>
          <div class="focus-note-card compact-note-card">
            <p>{{ dataStatusNote }}</p>
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
            <h2>重点关注企业</h2>
          </div>
          <span class="badge-subtle">优先看这些</span>
        </div>
        <div class="radar-list" v-if="rankingRows.length">
          <div v-for="item in rankingRows" :key="item.company_code" class="radar-item">
            <div class="radar-head">
              <strong>{{ item.company_name }}</strong>
              <span>{{ scoreText(item.total_score) }}</span>
            </div>
            <div class="bar-track"><div class="bar-fill" :style="{ width: `${Math.max(18, Number(item.total_score) || 0)}%` }"></div></div>
            <div class="radar-meta">
              <span>{{ item.risk_level }}风险</span>
              <RouterLink :to="`/workbench/${item.company_code}`">进入分析</RouterLink>
            </div>
          </div>
        </div>
      </div>

      <div class="cockpit-panel queue-panel">
        <div class="panel-header-row">
          <div>
            <p class="section-tag">Watch Queue</p>
            <h2>优先观察</h2>
          </div>
          <span class="badge-subtle">建议先看</span>
        </div>
        <div class="queue-list" v-if="watchlistRows.length">
          <div v-for="item in watchlistRows" :key="item.company_code" class="queue-card">
            <div class="trace-title-row">
              <strong>{{ item.company_name }}</strong>
              <span>{{ item.risk_level }}风险</span>
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
import type { AIEngineSummary, AIStackSummaryResponse, QualitySummaryResponse, RiskModelSummaryResponse, TargetCompany } from '../api/types';
import AgentWorkspacePanel from '../components/AgentWorkspacePanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';
import { useDashboardStore } from '../stores/dashboard';

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
const router = useRouter();
const qualitySummary = ref<QualitySummaryResponse | null>(null);
const riskModelSummary = ref<RiskModelSummaryResponse | null>(null);
const aiStack = ref<AIStackSummaryResponse | null>(null);
const selectedCode = ref('');

const rankingRows = computed<RankingRow[]>(() => ((store.payload?.ranking || []) as unknown as RankingRow[]).slice(0, 5));
const watchlistRows = computed<WatchRow[]>(() => ((store.payload?.watchlist || []) as unknown as WatchRow[]).slice(0, 4));
const currentCompany = computed<TargetCompany | null>(() => {
  return store.targets.find((item) => String(item.company_code) === selectedCode.value) || null;
});
const currentRanking = computed<RankingRow | null>(() => {
  return ((store.payload?.ranking || []) as unknown as RankingRow[]).find((item) => String(item.company_code) === selectedCode.value) || null;
});
const currentTaskLabel = computed(() => taskModeLabels[agentStore.taskMode || 'company_diagnosis'] || '企业诊断');
const currentRiskText = computed(() => currentRanking.value ? `${currentRanking.value.risk_level}风险` : '待分析');
const currentScoreText = computed(() => currentRanking.value ? scoreText(currentRanking.value.total_score) : '待分析');
const focusSummaryText = computed(() => {
  if (!currentCompany.value) return '请先选择一家企业。';
  if (currentRanking.value?.risk_level === '高') return '这家公司当前风险信号偏强，建议先从风险预警开始。';
  if (agentStore.taskMode === 'company_decision_brief') return '当前更适合围绕经营动作、投入重点和管理层决策来追问。';
  return '当前可以直接围绕经营状态、风险变化和行业趋势连续追问。';
});
const reportReadinessText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return qualitySummary.value.official_report_coverage_ratio >= 0.8 ? '最近年度已覆盖' : '仍在补齐';
});
const researchReadinessText = computed(() => {
  const total = (store.payload?.metrics?.research_report_count || 0) + (store.payload?.metrics?.industry_report_count || 0);
  return total ? `${total} 份公开资料` : '正在汇总';
});
const multimodalCoverageRatio = computed(() => qualitySummary.value?.multimodal_extract_coverage_ratio ?? 0);
const multimodalCoverageText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${Math.round((qualitySummary.value.multimodal_extract_coverage_ratio || 0) * 100)}%`;
});
const issueDigestText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  if (qualitySummary.value.pending_review_count <= 3) return '少量提醒';
  if (qualitySummary.value.pending_review_count <= 8) return `${qualitySummary.value.pending_review_count} 项提醒`;
  return '提醒较多';
});
const dataStatusNote = computed(() => {
  if (!qualitySummary.value) return '正在汇总当前可用资料。';
  if (qualitySummary.value.pending_review_count >= 8) return '当前数据提醒较多，建议先围绕覆盖完整的企业做结论。';
  if (qualitySummary.value.multimodal_extract_coverage_ratio < 0.5) return '复杂图表仍在持续补齐，遇到图表型问题时建议结合企业详情页一起看。';
  return '当前资料已经足够支撑经营判断、风险拆解和同业对比。';
});
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
const seedQuestion = computed(() => {
  const company = currentCompany.value;
  return company ? `${company.company_name}当前最值得关注的经营问题是什么？` : '当前最值得关注的经营问题是什么？';
});
const visibleEngines = computed<AIEngineSummary[]>(() => (aiStack.value?.engines || []).slice(0, 4));

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

function riskFlagText(value: unknown) {
  const flags = Array.isArray(value) ? value : [];
  return flags.length ? flags.join('；') : '当前没有高优先级风险提示。';
}

function ringStyle(value: number, color: string, base: string) {
  const angle = Math.max(0, Math.min(100, value * 100));
  return {
    background: `conic-gradient(${color} ${angle}%, ${base} ${angle}% 100%)`,
  };
}

async function applyMission(mode: 'risk' | 'compare' | 'growth') {
  const company = currentCompany.value;
  if (mode === 'compare') {
    await router.push({ name: 'compare' });
    return;
  }
  if (!company) return;
  const prompts = {
    risk: `把${company.company_name}的风险拆成财务、经营、行业三层并给出动作建议`,
    growth: `${company.company_name}未来两年的主要机会、变量和投入重点是什么？`,
  };
  agentStore.resetThread(String(company.company_code), company.company_name);
  await agentStore.ask(prompts[mode], {
    companyCode: String(company.company_code),
    companyName: company.company_name,
    taskMode: mode === 'risk' ? 'company_risk_forecast' : 'company_decision_brief',
  });
}

watch(selectedCode, (value) => {
  const company = store.targets.find((item) => String(item.company_code) === value);
  if (company) {
    agentStore.setFocus(String(company.company_code), company.company_name);
    if (!agentStore.threadId) {
      agentStore.resetThread(String(company.company_code), company.company_name);
    }
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
