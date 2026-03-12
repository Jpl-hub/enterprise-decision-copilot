<template>
  <div class="page-stack overview-page cockpit-overview">
    <section class="cockpit-hero-board">
      <aside class="cockpit-side-panel">
        <div class="cockpit-focus-card">
          <div class="cockpit-focus-head">
            <div>
              <h3>{{ currentCompany?.company_name || '请选择企业' }}</h3>
            </div>
            <span class="badge-subtle">{{ formatExchange(currentCompany?.exchange) }}</span>
          </div>

          <label class="console-field analysis-company-picker">
            <span>分析企业</span>
            <select v-model="selectedCode" class="select-input hero-select">
              <option v-for="item in store.targets" :key="item.company_code" :value="String(item.company_code)">{{ item.company_name }}</option>
            </select>
          </label>

          <div class="cockpit-focus-tags" v-if="currentCompany">
            <span class="analysis-focus-pill">{{ formatIndustry(currentCompany.industry) }}</span>
            <span class="analysis-focus-pill">{{ currentTaskLabel }}</span>
            <span class="analysis-focus-pill">{{ currentRiskText }}</span>
            <span class="analysis-focus-pill">{{ currentScoreText }}</span>
          </div>

          <div class="cockpit-focus-stats">
            <div class="cockpit-mini-stat">
              <span>证据吞吐</span>
              <strong>{{ evidenceVolumeText }}</strong>
            </div>
            <div class="cockpit-mini-stat">
              <span>模型 AUC</span>
              <strong>{{ riskAucText }}</strong>
            </div>
            <div class="cockpit-mini-stat">
              <span>多模态</span>
              <strong>{{ multimodalCoverageText }}</strong>
            </div>
          </div>
        </div>
      </aside>

      <article class="cockpit-stage-panel cockpit-agent-stage">
        <div class="cockpit-stage-head">
          <div>
            <h2>企业运营分析与决策中枢</h2>
          </div>
          <div class="cockpit-stage-kpis">
            <span>{{ latestOfficialText }}</span>
          </div>
        </div>

        <div class="cockpit-stage-action-grid">
          <RouterLink
            v-for="item in cockpitRoutes"
            :key="item.title"
            :to="item.to"
            class="cockpit-stage-action"
          >
            <strong>{{ item.title }}</strong>
          </RouterLink>
        </div>

        <div class="cockpit-scene-grid">
          <button
            v-for="item in interactionScenes"
            :key="item.title"
            type="button"
            class="cockpit-scene-card"
            @click="activateInteractionScene(item)"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.title }}</strong>
            <p>{{ item.prompt }}</p>
          </button>
        </div>

        <AgentWorkspacePanel
          :company-code="currentCompany?.company_code ? String(currentCompany.company_code) : null"
          :company-name="currentCompany?.company_name"
          :seed-question="seedQuestion"
          title=""
          eyebrow=""
          placeholder="直接提问，例如：这家公司最值得盯的经营问题是什么？"
        />
      </article>

      <aside class="cockpit-side-panel">
        <div class="cockpit-timing-card">
          <div class="cockpit-focus-head">
            <div>
              <h3>时效与披露</h3>
            </div>
            <span class="badge-subtle">{{ latestOfficialText }}</span>
          </div>

          <div class="cockpit-timing-grid">
            <div class="cockpit-timing-item">
              <span>年报</span>
              <strong>{{ annualReportText }}</strong>
            </div>
            <div class="cockpit-timing-item">
              <span>个股研报</span>
              <strong>{{ researchFreshnessText }}</strong>
            </div>
            <div class="cockpit-timing-item">
              <span>行业研报</span>
              <strong>{{ industryFreshnessText }}</strong>
            </div>
            <div class="cockpit-timing-item">
              <span>宏观窗口</span>
              <strong>{{ macroFreshnessText }}</strong>
            </div>
          </div>

          <div class="cockpit-period-list">
            <div v-for="item in freshnessPeriods" :key="item.period_type" class="cockpit-period-row">
              <span>{{ item.period_label }}</span>
              <strong>{{ item.covered_companies }}/{{ store.targets.length }}</strong>
            </div>
          </div>
        </div>

        <div class="cockpit-alert-card">
          <div class="cockpit-focus-head">
            <div>
              <h3>重点盯防</h3>
            </div>
            <RouterLink to="/quality" class="text-link-button">查看治理台</RouterLink>
          </div>

          <div class="watchtower-list">
            <RouterLink
              v-for="item in watchlistRows.slice(0, 3)"
              :key="item.company_code"
              :to="`/workbench/${item.company_code}`"
              class="watchtower-card cockpit-link-card"
            >
              <div class="trace-title-row">
                <strong>{{ item.company_name }}</strong>
                <span class="badge-subtle">{{ item.risk_level }}风险</span>
              </div>
              <p>{{ getRiskFlagsText(item.risk_flags) }}</p>
            </RouterLink>
          </div>
        </div>
      </aside>
    </section>

    <section class="competition-visual-board">
      <article class="support-panel dark-panel competition-visual-panel competition-ring-panel">
        <div class="panel-header-row compact-panel-header">
          <div>
            <h3>系统能力</h3>
          </div>
          <RouterLink to="/quality" class="text-link-button">查看系统底座</RouterLink>
        </div>
        <EChartPanel :option="capabilityRingOption" height="340px" @chart-click="handleCapabilityChartClick" />
        <div class="competition-metric-strip">
          <div v-for="item in aiPillarHighlights" :key="item.name" class="competition-metric-card">
            <span>{{ item.name }}</span>
            <strong>{{ item.score }}</strong>
            <p>{{ item.summary }}</p>
          </div>
        </div>
      </article>

      <div class="competition-visual-grid">
        <article class="support-panel dark-panel competition-visual-panel">
          <div class="panel-header-row compact-panel-header">
            <div>
              <h3>企业分布</h3>
            </div>
          </div>
          <EChartPanel :option="companyMatrixOption" height="320px" @chart-click="handleCompanyMatrixClick" />
        </article>

        <article class="support-panel dark-panel competition-visual-panel">
          <div class="panel-header-row compact-panel-header">
            <div>
              <h3>数据时效</h3>
            </div>
          </div>
          <EChartPanel :option="freshnessPulseOption" height="320px" @chart-click="handleFreshnessChartClick" />
        </article>
      </div>
    </section>

    <section class="overview-intel-grid cockpit-intel-grid">
      <article class="support-panel dark-panel">
        <div class="panel-header-row compact-panel-header">
          <div>
            <h3>行业热度</h3>
          </div>
        </div>

        <div class="heat-list" v-if="industryHeatRows.length">
          <button
            v-for="item in industryHeatRows"
            :key="item.industry_name"
            type="button"
            class="heat-card cockpit-action-card"
            @click="primeAgentPrompt(buildIndustryPrompt(item.industry_name), 'industry_trend')"
          >
            <div class="trace-title-row">
              <strong>{{ formatIndustry(item.industry_name) }}</strong>
              <span>{{ item.report_count }} 篇</span>
            </div>
            <div class="bar-track"><div class="bar-fill" :style="{ width: heatWidth(item.report_count, industryHeatMax) }"></div></div>
            <p>正向 {{ item.positive_count }} · 负向 {{ item.negative_count }} · 最新 {{ formatDate(item.latest_report_date) }}</p>
          </button>
        </div>
      </article>

      <article class="support-panel dark-panel">
        <div class="panel-header-row compact-panel-header">
          <div>
            <h3>企业关注度</h3>
          </div>
        </div>

        <div class="heat-list" v-if="companyResearchRows.length">
          <RouterLink
            v-for="item in companyResearchRows"
            :key="item.company_code"
            :to="`/workbench/${item.company_code}`"
            class="heat-card cockpit-link-card"
          >
            <div class="trace-title-row">
              <strong>{{ item.company_name }}</strong>
              <span>{{ item.report_count }} 篇</span>
            </div>
            <div class="bar-track"><div class="bar-fill" :style="{ width: heatWidth(item.report_count, companyResearchMax) }"></div></div>
            <p>正向 {{ item.positive_count }} · 负向 {{ item.negative_count }} · 最新 {{ formatDate(item.latest_report_date) }}</p>
          </RouterLink>
        </div>
      </article>

      <article class="support-panel dark-panel">
        <div class="panel-header-row compact-panel-header">
          <div>
            <h3>宏观信号</h3>
          </div>
        </div>

        <div class="macro-pulse-list" v-if="macroRows.length">
          <button
            v-for="item in macroRows"
            :key="String(item.indicator_name)"
            type="button"
            class="macro-pulse-card cockpit-action-card"
            @click="primeAgentPrompt(buildMacroPrompt(item), 'company_decision_brief')"
          >
            <span>{{ String(item.indicator_name || '指标') }}</span>
            <strong>{{ formatMacroValue(item.indicator_value, item.unit) }}</strong>
            <p>{{ macroFreshnessText }}</p>
          </button>
        </div>
      </article>
    </section>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

import { api } from '../api/client';
import type { AIStackSummaryResponse, QualitySummaryResponse, RiskModelSummaryResponse, WarehouseOverviewResponse } from '../api/types';
import AgentWorkspacePanel from '../components/AgentWorkspacePanel.vue';
import EChartPanel from '../components/EChartPanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';
import { useDashboardStore } from '../stores/dashboard';

interface RankingRow {
  company_code: string;
  company_name: string;
  total_score: number;
  risk_level: string;
}

interface WatchlistRow {
  company_code: string;
  company_name: string;
  risk_level: string;
  risk_flags?: string[];
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
const selectedCode = ref('');
const seedQuestionOverride = ref('');
const aiStackSummary = ref<AIStackSummaryResponse | null>(null);
const qualitySummary = ref<QualitySummaryResponse | null>(null);
const riskModelSummary = ref<RiskModelSummaryResponse | null>(null);
const warehouseOverview = ref<WarehouseOverviewResponse | null>(null);

const dashboardMetrics = computed(() => store.payload?.metrics || null);
const rankingRows = computed<RankingRow[]>(() => ((store.payload?.ranking || []) as unknown as RankingRow[]).slice(0, 5));
const watchlistRows = computed<WatchlistRow[]>(() => ((store.payload?.watchlist || []) as unknown as WatchlistRow[]).slice(0, 5));
const dashboardFreshness = computed(() => store.payload?.freshness || null);
const freshnessPeriods = computed(() => dashboardFreshness.value?.period_summaries || []);
const macroRows = computed<Array<Record<string, unknown>>>(() => (store.payload?.macro || []).slice(0, 4) as Array<Record<string, unknown>>);
const industryHeatRows = computed(() => warehouseOverview.value?.industry_heat?.slice(0, 5) || []);
const companyResearchRows = computed(() => warehouseOverview.value?.company_research_heat?.slice(0, 5) || []);
const industryHeatMax = computed(() => Math.max(...industryHeatRows.value.map((item) => item.report_count), 1));
const companyResearchMax = computed(() => Math.max(...companyResearchRows.value.map((item) => item.report_count), 1));
const currentCompany = computed(() => store.targets.find((item) => String(item.company_code) === selectedCode.value) || null);
const currentRanking = computed<RankingRow | null>(() => {
  return ((store.payload?.ranking || []) as unknown as RankingRow[]).find((item) => String(item.company_code) === selectedCode.value) || null;
});
const currentTaskLabel = computed(() => taskModeLabels[agentStore.taskMode || 'company_diagnosis'] || '企业诊断');
const currentRiskText = computed(() => currentRanking.value ? `${currentRanking.value.risk_level}风险` : '待分析');
const currentScoreText = computed(() => currentRanking.value ? scoreText(currentRanking.value.total_score) : '待分析');
const comparePeerCode = computed(() => {
  const leaderCode = rankingRows.value[0]?.company_code ? String(rankingRows.value[0].company_code) : '';
  if (!selectedCode.value) return leaderCode;
  if (leaderCode && leaderCode !== selectedCode.value) return leaderCode;
  return rankingRows.value.find((item) => String(item.company_code) !== selectedCode.value)?.company_code || leaderCode;
});
const compareRoute = computed(() => {
  const codes = [selectedCode.value, String(comparePeerCode.value || '')].filter(Boolean);
  return { path: '/compare', query: codes.length >= 2 ? { companies: codes.join(',') } : {} };
});
const cockpitRoutes = computed(() => [
  {
    tag: 'Workbench',
    title: '企业详情',
    body: '进入企业工作台，看经营、风险与证据全景。',
    to: selectedCode.value ? `/workbench/${selectedCode.value}` : '/workbench',
  },
  {
    tag: 'Compare',
    title: '对比决策',
    body: '和当前高分企业做横向对照，直接进入对比台。',
    to: compareRoute.value,
  },
  {
    tag: 'Package',
    title: '导出报告',
    body: '导出当前企业的结构化分析材料和证据包。',
    to: selectedCode.value ? `/competition/${selectedCode.value}` : '/competition',
  },
  {
    tag: 'Quality',
    title: '数据治理',
    body: '查看真实披露、图表补全与治理缺口。',
    to: '/quality',
  },
]);
const interactionScenes = computed(() => {
  const companyName = currentCompany.value?.company_name || '当前企业';
  return [
    {
      label: '管理层晨会',
      title: '先看经营动作',
      prompt: `如果今天开经营会，${companyName}最该先讨论什么？`,
      taskMode: 'company_decision_brief',
    },
    {
      label: '投研快览',
      title: '先看横向差异',
      prompt: `把${companyName}和当前高分同行放在一起，先看最关键的差异。`,
      taskMode: 'company_diagnosis',
    },
    {
      label: '风控巡检',
      title: '先看风险与缺口',
      prompt: `从风险和数据可信度两个角度，判断${companyName}当前最该盯的信号。`,
      taskMode: 'company_risk_forecast',
    },
  ];
});
const seedQuestion = computed(() => {
  if (seedQuestionOverride.value) return seedQuestionOverride.value;
  return currentCompany.value ? `${currentCompany.value.company_name}当前最值得关注的经营问题是什么？` : '当前最值得关注的经营问题是什么？';
});
const riskAucText = computed(() => riskModelSummary.value?.metrics?.roc_auc?.toFixed(3) || '暂无');
const multimodalCoverageText = computed(() => {
  if (!qualitySummary.value) return '加载中';
  return `${Math.round((qualitySummary.value.multimodal_extract_coverage_ratio || 0) * 100)}%`;
});
const evidenceVolumeText = computed(() => {
  if (!dashboardMetrics.value) return '待刷新';
  return `${dashboardMetrics.value.research_report_count + dashboardMetrics.value.industry_report_count} 份`;
});
const annualReportText = computed(() => dashboardFreshness.value?.annual_report_year ? `${dashboardFreshness.value.annual_report_year} 年报` : '待刷新');
const annualPublishText = computed(() => dashboardFreshness.value?.annual_report_published_at ? `披露日 ${formatDate(dashboardFreshness.value.annual_report_published_at)}` : '尚未识别到官方年报时间');
const researchFreshnessText = computed(() => formatDate(dashboardFreshness.value?.latest_research_report));
const industryFreshnessText = computed(() => formatDate(dashboardFreshness.value?.latest_industry_report));
const macroFreshnessText = computed(() => dashboardFreshness.value?.latest_macro_period || '待刷新');
const latestOfficialText = computed(() => {
  if (!dashboardFreshness.value?.latest_official_disclosure) return '官方披露待更新';
  return `${dashboardFreshness.value.latest_periodic_label || '定期报告'}更新到 ${formatDate(dashboardFreshness.value.latest_official_disclosure)}`;
});
const aiPillars = computed(() => aiStackSummary.value?.pillars || []);
const aiPillarHighlights = computed(() => aiPillars.value.slice(0, 3).map((item) => ({
  name: item.name,
  score: `${item.readiness_score}`,
  summary: item.summary,
})));
const capabilityRingOption = computed(() => {
  const pillars = aiPillars.value.slice(0, 3);
  const palette = ['#4cc9f0', '#4ade80', '#f59e0b'];
  const series = pillars.flatMap((item, index) => {
    const outer = 86 - index * 20;
    const inner = outer - 11;
    const value = Math.max(0, Math.min(100, item.readiness_score || 0));
    return [
      {
        type: 'pie',
        radius: [`${inner}%`, `${outer}%`],
        center: ['32%', '48%'],
        silent: false,
        clockwise: true,
        startAngle: 90,
        label: { show: false },
        itemStyle: { borderWidth: 0 },
        data: [
          {
            value,
            name: item.name,
            itemStyle: {
              color: palette[index],
              shadowBlur: 18,
              shadowColor: palette[index],
            },
            pillarId: item.pillar_id,
          },
          {
            value: 100 - value,
            name: `${item.name}-rest`,
            itemStyle: { color: 'rgba(148, 163, 184, 0.12)' },
            tooltip: { show: false },
          },
        ],
      },
    ];
  });

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (params: { name?: string; value?: number; data?: { pillarId?: string } }) => {
        if (!params?.data?.pillarId) return '';
        return `${params.name}：${params.value} / 100`;
      },
    },
    graphic: [
      {
        type: 'text',
        left: '23%',
        top: '39%',
        style: {
          text: '系统\n底座',
          fill: '#f8fbff',
          font: '700 24px "Segoe UI Variable"',
          align: 'center',
          lineHeight: 34,
        },
      },
    ],
    series,
  } as const;
});
const companyMatrixOption = computed(() => {
  const attentionMap = new Map(companyResearchRows.value.map((item) => [String(item.company_code), item.report_count]));
  const riskOrdinal: Record<string, number> = { 低: 0, 中: 1, 高: 2 };
  const scatterData = rankingRows.value.map((item) => ({
    value: [
      Number(item.total_score || 0),
      riskOrdinal[item.risk_level] ?? 1,
      attentionMap.get(String(item.company_code)) || 12,
    ],
    name: item.company_name,
    companyCode: item.company_code,
    riskLevel: item.risk_level,
  }));
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (params: { data?: { name?: string; riskLevel?: string; value?: [number, number, number] } }) => {
        const data = params.data;
        if (!data) return '';
        return `${data.name}<br/>综合分：${data.value?.[0]?.toFixed?.(1) || data.value?.[0]}<br/>风险：${data.riskLevel}<br/>关注度：${data.value?.[2]}`;
      },
    },
    grid: { left: 46, right: 16, top: 30, bottom: 38 },
    xAxis: {
      name: '综合得分',
      nameTextStyle: { color: '#9fc0df' },
      axisLabel: { color: '#c5d8ea' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.14)' } },
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.26)' } },
    },
    yAxis: {
      name: '风险等级',
      nameTextStyle: { color: '#9fc0df' },
      min: -0.3,
      max: 2.3,
      interval: 1,
      axisLabel: {
        color: '#c5d8ea',
        formatter: (value: number) => ['低', '中', '高'][value] || '',
      },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.14)' } },
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.26)' } },
    },
    series: [
      {
        type: 'scatter',
        data: scatterData,
        symbolSize: (value: number[]) => Math.max(18, Math.min(42, value[2] / 1.8)),
        label: {
          show: true,
          formatter: (params: { data?: { name?: string } }) => params.data?.name || '',
          color: '#f8fbff',
          fontSize: 12,
          position: 'top',
        },
        itemStyle: {
          color: '#4cc9f0',
          shadowBlur: 18,
          shadowColor: 'rgba(76, 201, 240, 0.5)',
          borderColor: 'rgba(255,255,255,0.82)',
          borderWidth: 1,
        },
      },
    ],
  } as const;
});
const freshnessPulseOption = computed(() => {
  const categories = [
    ...freshnessPeriods.value.map((item) => item.period_label),
    '图表补全',
    '全局覆盖',
  ];
  const coverageValues = [
    ...freshnessPeriods.value.map((item) => Math.round((item.coverage_ratio || 0) * 100)),
    Math.round((qualitySummary.value?.multimodal_extract_coverage_ratio || 0) * 100),
    Math.round((qualitySummary.value?.official_report_coverage_ratio || 0) * 100),
  ];
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: { left: 36, right: 18, top: 26, bottom: 34 },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { color: '#c5d8ea', interval: 0 },
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.26)' } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { color: '#c5d8ea', formatter: '{value}%' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.14)' } },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'line',
        smooth: true,
        data: coverageValues,
        symbol: 'circle',
        symbolSize: 10,
        lineStyle: {
          width: 4,
          color: '#4ade80',
        },
        itemStyle: {
          color: '#4ade80',
          shadowBlur: 16,
          shadowColor: 'rgba(74, 222, 128, 0.5)',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(74, 222, 128, 0.34)' },
              { offset: 1, color: 'rgba(74, 222, 128, 0.02)' },
            ],
          },
        },
      },
    ],
  } as const;
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

function formatMacroValue(value: unknown, unit?: unknown) {
  const num = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(num)) return '待刷新';
  const suffix = typeof unit === 'string' ? unit : '';
  return `${num}${suffix}`;
}

function formatDate(value?: string | null) {
  if (!value) return '待刷新';
  return String(value).replace('T', ' ').slice(0, 10);
}

function getRiskFlagsText(flags?: string[]) {
  if (!flags?.length) return '当前未触发显著风险标记，但仍建议持续跟踪经营与行业变量。';
  return flags.slice(0, 2).join('；');
}

function heatWidth(value: number, max: number) {
  return `${Math.max(12, (value / Math.max(max, 1)) * 100)}%`;
}

function buildIndustryPrompt(industryName?: string | null) {
  const industry = formatIndustry(industryName);
  const companyName = currentCompany.value?.company_name || '当前企业';
  return `结合${industry}赛道的最新研报热度，判断${companyName}接下来最需要盯的行业变量与机会风险。`;
}

function buildMacroPrompt(item: Record<string, unknown>) {
  const indicator = String(item.indicator_name || '宏观指标');
  const companyName = currentCompany.value?.company_name || '当前企业';
  return `宏观指标“${indicator}”对${companyName}接下来的经营判断和动作建议有什么影响？`;
}

function focusAgentStage() {
  document.querySelector('.cockpit-agent-stage')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function primeAgentPrompt(question: string, taskMode: string) {
  seedQuestionOverride.value = question;
  agentStore.setTaskMode(taskMode);
  focusAgentStage();
}

function activateInteractionScene(item: { prompt: string; taskMode: string }) {
  primeAgentPrompt(item.prompt, item.taskMode);
}

function handleCapabilityChartClick(params: Record<string, unknown>) {
  const data = params.data as { pillarId?: string } | undefined;
  if (!data?.pillarId) return;
  void router.push('/quality');
}

function handleCompanyMatrixClick(params: Record<string, unknown>) {
  const data = params.data as { companyCode?: string } | undefined;
  if (!data?.companyCode) return;
  void router.push(`/workbench/${data.companyCode}`);
}

function handleFreshnessChartClick(params: Record<string, unknown>) {
  const category = String(params.name || '');
  if (!category) return;
  primeAgentPrompt(`从${category}这个数据环节出发，判断当前系统最需要补强的证据和治理动作。`, 'data_quality');
}

watch(selectedCode, (value, previous) => {
  const company = store.targets.find((item) => String(item.company_code) === value);
  if (!company) return;
  const companyCode = String(company.company_code);
  const shouldPreserveExistingThread =
    Boolean(agentStore.threadId) &&
    previous === '' &&
    agentStore.focusCompanyCode === companyCode;
  if (value !== previous) {
    seedQuestionOverride.value = '';
  }
  agentStore.setFocus(companyCode, company.company_name);
  if (value !== previous && !shouldPreserveExistingThread) {
    agentStore.resetThread(companyCode, company.company_name);
  }
});

onMounted(async () => {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  if (!selectedCode.value && store.targets.length) {
    const existingFocus = agentStore.focusCompanyCode ? String(agentStore.focusCompanyCode) : '';
    const defaultCode = store.targets.some((item) => String(item.company_code) === existingFocus)
      ? existingFocus
      : String(store.targets[0].company_code);
    selectedCode.value = defaultCode;
    const company = currentCompany.value;
    const shouldPreserveExistingThread = Boolean(agentStore.threadId) && defaultCode === existingFocus;
    if (company && !shouldPreserveExistingThread) {
      agentStore.resetThread(String(company.company_code), company.company_name);
    }
  }
  const [stack, quality, riskSummary, warehouse] = await Promise.all([
    api.getAIStack(),
    api.getQualitySummary(),
    api.getRiskModelSummary(),
    api.getWarehouseOverview(8),
  ]);
  aiStackSummary.value = stack;
  qualitySummary.value = quality;
  riskModelSummary.value = riskSummary;
  warehouseOverview.value = warehouse;
});
</script>
