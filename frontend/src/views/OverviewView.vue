<template>
  <div class="page-stack overview-page">
    <section class="hero-panel">
      <div class="hero-copy">
        <p class="section-tag">Agent Command</p>
        <h2>先给结论，再给证据，再给行动建议。</h2>
        <p class="hero-text">
          面向医药行业企业运营分析场景，系统把官方财报、研究报告、宏观指标、多模态抽取和风险模型编排成一个可追溯的 Agent 决策流程。
        </p>
        <div class="hero-command">
          <input
            v-model="question"
            class="text-input hero-input"
            placeholder="例如：结合行业研报和财报，判断迈瑞医疗未来两年的经营风险与机会"
            @keydown.enter="runAgent"
          />
          <button class="button-primary hero-button" @click="runAgent" :disabled="agentLoading">发起分析</button>
        </div>
        <div class="quick-prompt-row">
          <button v-for="prompt in quickPrompts" :key="prompt" class="button-ghost chip-button" @click="applyPrompt(prompt)">
            {{ prompt }}
          </button>
        </div>
      </div>
      <div class="hero-side">
        <div class="hero-highlight-card">
          <p class="section-tag">Product Logic</p>
          <ul class="hero-list">
            <li>用户先提问题，系统再自动调度报告、风险、检索和治理链路。</li>
            <li>结论必须有证据，证据必须能回到原始来源和抽取记录。</li>
            <li>不仅给判断，还要能继续追问、对比和复核。</li>
          </ul>
        </div>
        <div class="hero-stat-strip" v-if="store.payload?.metrics">
          <div class="hero-stat">
            <span>企业样本</span>
            <strong>{{ store.payload.metrics.sample_count }}</strong>
          </div>
          <div class="hero-stat">
            <span>个股研报</span>
            <strong>{{ store.payload.metrics.research_report_count }}</strong>
          </div>
          <div class="hero-stat">
            <span>行业研报</span>
            <strong>{{ store.payload.metrics.industry_report_count }}</strong>
          </div>
        </div>
      </div>
    </section>

    <section class="three-card-grid">
      <RouterLink to="/workbench" class="capability-card capability-card-agent">
        <p class="section-tag">01</p>
        <h3>企业分析主入口</h3>
        <p>围绕单家企业展开综合报告、决策简报、风险预测和 Agent 深问，不再让用户自己拼页面。</p>
      </RouterLink>
      <RouterLink to="/compare" class="capability-card capability-card-compare">
        <p class="section-tag">02</p>
        <h3>竞争格局与对比</h3>
        <p>直接比较多家企业的盈利、成长、研发、韧性和风险，不让用户在多页中来回跳转。</p>
      </RouterLink>
      <RouterLink to="/quality" class="capability-card capability-card-data">
        <p class="section-tag">03</p>
        <h3>数据治理与可信度</h3>
        <p>展示官方财报覆盖、多模态抽取、异常复核和人工治理队列，把“结论可信”讲透。</p>
      </RouterLink>
    </section>

    <PagePanel title="Agent 回答" eyebrow="Response" description="首页直接展示 Agent 输出，让用户先感受到这是一个智能体产品。">
      <div v-if="agentLoading" class="empty-state">正在编排工具链并生成答案...</div>
      <div v-else-if="agentResult" class="panel-split two-cols agent-answer-grid">
        <div class="sub-panel emphasis-panel">
          <p class="section-tag">Answer</p>
          <h3>{{ agentResult.title }}</h3>
          <p class="panel-description strong-copy">{{ agentResult.summary }}</p>
          <div class="stack-list" v-if="agentResult.highlights.length">
            <div v-for="item in agentResult.highlights.slice(0, 5)" :key="item" class="info-card compact answer-card">
              <p>{{ item }}</p>
            </div>
          </div>
        </div>
        <div class="sub-panel">
          <p class="section-tag">Execution Trace</p>
          <TracePanel :trace="agentResult.trace" />
        </div>
      </div>
      <div v-else class="empty-state">输入一个经营问题，系统会自动调用企业分析、检索、风险和质量治理链路。</div>
    </PagePanel>

    <PagePanel title="系统能力地图" eyebrow="Architecture" description="把 Agent、Data、AI 三条主线摆清楚，而不是堆杂乱数字。">
      <div class="architecture-grid">
        <div class="pillar-card">
          <p class="section-tag">Agent</p>
          <h3>决策编排层</h3>
          <ul class="pillar-list">
            <li>意图识别 + 工具路由 + 执行轨迹</li>
            <li>企业报告、风险预测、质量治理统一入口</li>
            <li>输出结论时附证据引用与追溯链</li>
          </ul>
        </div>
        <div class="pillar-card">
          <p class="section-tag">AI</p>
          <h3>多模态与预测层</h3>
          <ul class="pillar-list">
            <li>多模态财报抽取进入正式治理流程</li>
            <li>研报语义召回与证据级引用</li>
            <li>表格模型 + 时序模型形成风险双引擎</li>
          </ul>
        </div>
        <div class="pillar-card">
          <p class="section-tag">Data</p>
          <h3>大数据工程层</h3>
          <ul class="pillar-list">
            <li>交易所财报、研报、宏观数据统一分层管理</li>
            <li>DuckDB 分析仓 + 质量中心 + 自动复核队列</li>
            <li>面向扩容赛道和后续分布式处理预留路径</li>
          </ul>
        </div>
      </div>
    </PagePanel>

    <PagePanel title="核心运行指标" eyebrow="Signals" description="只保留用户真正需要判断系统状态的关键信号。">
      <div class="signal-grid">
        <div class="signal-card" v-if="store.payload?.metrics">
          <span class="signal-label">运营分析覆盖</span>
          <strong>{{ store.payload.metrics.sample_count }}</strong>
          <p>已纳入企业样本，最新年度 {{ store.payload.metrics.latest_year }}</p>
        </div>
        <div class="signal-card" v-if="qualitySummary">
          <span class="signal-label">多模态抽取</span>
          <strong>{{ `${(qualitySummary.multimodal_extract_coverage_ratio * 100).toFixed(0)}%` }}</strong>
          <p>已覆盖 {{ qualitySummary.multimodal_extract_report_count }} / {{ qualitySummary.multimodal_expected_report_count }} 份年报</p>
        </div>
        <div class="signal-card" v-if="riskModel">
          <span class="signal-label">风险模型 AUC</span>
          <strong>{{ formatMetric(riskModel.metrics.roc_auc, 3) }}</strong>
          <p>{{ riskModel.model_type || 'tabular model' }}，训练样本 {{ riskModel.sample_count }}</p>
        </div>
        <div class="signal-card" v-if="warehouse">
          <span class="signal-label">分析仓就绪</span>
          <strong>{{ warehouse.table_count }}</strong>
          <p>张表已入仓，支撑查询、治理和材料导出</p>
        </div>
      </div>
    </PagePanel>

    <PagePanel title="重点观察企业" eyebrow="Targets" description="把用户带到具体业务对象，而不是让他在首页迷路。">
      <div class="target-spotlight-grid" v-if="store.payload?.targets?.length">
        <div v-for="item in store.payload.targets.slice(0, 6)" :key="item.company_code" class="target-spotlight-card">
          <div class="trace-title-row">
            <strong>{{ item.company_name }}</strong>
            <span class="badge-subtle">{{ item.exchange }}</span>
          </div>
          <p class="muted">{{ item.segment }} · {{ item.industry }}</p>
          <div class="button-row left-align">
            <RouterLink class="button-ghost" :to="`/workbench/${item.company_code}`">进入企业分析</RouterLink>
            <RouterLink class="button-ghost" :to="`/competition/${item.company_code}`">导出分析材料</RouterLink>
          </div>
        </div>
      </div>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';

import { api } from '../api/client';
import type { AgentResponse, QualitySummaryResponse, RiskModelSummaryResponse, WarehouseOverviewResponse } from '../api/types';
import PagePanel from '../components/PagePanel.vue';
import TracePanel from '../components/TracePanel.vue';
import { useDashboardStore } from '../stores/dashboard';

const store = useDashboardStore();
const agentLoading = ref(false);
const agentResult = ref<AgentResponse | null>(null);
const warehouse = ref<WarehouseOverviewResponse | null>(null);
const riskModel = ref<RiskModelSummaryResponse | null>(null);
const qualitySummary = ref<QualitySummaryResponse | null>(null);
const question = ref('结合行业研报与财报，判断迈瑞医疗未来两年的经营风险与机会');

const quickPrompts = [
  '分析迈瑞医疗当前经营韧性',
  '比较迈瑞医疗和联影医疗谁更值得跟踪',
  '系统数据质量覆盖和多模态抽取情况怎么样',
];

function applyPrompt(prompt: string) {
  question.value = prompt;
  void runAgent();
}

function formatMetric(value: number | null | undefined, digits = 2) {
  return value == null ? '暂无' : value.toFixed(digits);
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

onMounted(async () => {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  const [warehouseResult, riskModelResult, qualityResult] = await Promise.all([
    api.getWarehouseOverview(),
    api.getRiskModelSummary(),
    api.getQualitySummary(),
  ]);
  warehouse.value = warehouseResult;
  riskModel.value = riskModelResult;
  qualitySummary.value = qualityResult;
  await runAgent();
});
</script>
