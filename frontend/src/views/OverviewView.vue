<template>
  <div class="overview-shell">
    <template v-if="isReady">
    <aside class="focus-rail panel-card">
      <div class="panel-head">
        <div>
          <p class="section-tag">当前聚焦</p>
          <h2>{{ currentCompany?.company_name || '请选择企业' }}</h2>
        </div>
        <span class="score-pill">{{ currentScoreText }}</span>
      </div>

      <label class="field-block">
        <span>分析目标</span>
        <select v-model="selectedCode" class="focus-select">
          <option value="" disabled>请选择企业</option>
          <option v-for="item in store.targets" :key="item.company_code" :value="String(item.company_code)">
            {{ item.company_name }}（{{ formatExchange(item.exchange) }}）
          </option>
        </select>
      </label>

      <div v-if="currentCompany" class="pill-row">
        <span class="soft-pill">{{ formatIndustry(currentCompany.industry) }}</span>
        <span class="soft-pill">{{ currentRiskText }}</span>
        <span class="soft-pill">{{ currentTaskLabel }}</span>
      </div>

      <div class="mini-grid">
        <div class="mini-card">
          <span>官方披露</span>
          <strong>{{ annualReportText }}</strong>
        </div>
        <div class="mini-card">
          <span>证据规模</span>
          <strong>{{ evidenceVolumeText }}</strong>
        </div>
      </div>

      <p class="focus-note">{{ latestOfficialText }}</p>

      <div v-if="watchlistRows.length" class="watch-stack">
        <div class="panel-head compact">
          <div>
            <p class="section-tag">重点盯防</p>
            <h3>风险哨位</h3>
          </div>
        </div>
        <RouterLink v-for="item in watchlistRows" :key="String(item.company_code)" :to="`/workbench/${String(item.company_code)}`" class="watch-item">
          <div>
            <strong>{{ item.company_name }}</strong>
            <p>{{ getRiskFlagsText(item.risk_flags) }}</p>
          </div>
          <span>{{ item.risk_level }}风险</span>
        </RouterLink>
      </div>
    </aside>

    <section class="command-stage">
      <div class="hero-panel">
        <div>
          <p class="section-tag">企业运营分析中枢</p>
          <h1>先问问题，再看证据，再做判断</h1>
          <p class="hero-copy">围绕 {{ currentCompany?.company_name || '目标企业' }} 直接发问，系统会串联财报、研报、风险与图表锚点，输出可回查的经营判断。</p>
        </div>
        <div class="hero-stats">
          <div class="hero-stat"><span>年报口径</span><strong>{{ annualReportText }}</strong><p>{{ annualPublishText }}</p></div>
          <div class="hero-stat"><span>研报时效</span><strong>{{ researchFreshnessText }}</strong><p>行业更新 {{ industryFreshnessText }}</p></div>
          <div class="hero-stat"><span>宏观周期</span><strong>{{ macroFreshnessText }}</strong><p>{{ latestOfficialText }}</p></div>
        </div>
      </div>

      <div class="scene-grid">
        <button v-for="item in interactionScenes" :key="item.label" type="button" class="scene-card" @click="activateInteractionScene(item)">
          <span>{{ item.label }}</span>
          <strong>{{ item.title }}</strong>
          <p>{{ item.prompt }}</p>
        </button>
      </div>

      <div v-if="currentCompany" class="route-grid">
        <RouterLink v-for="item in cockpitRoutes" :key="item.title" :to="item.to" class="route-card">
          <div>
            <span>{{ item.tag }}</span>
            <strong>{{ item.title }}</strong>
            <p>{{ item.body }}</p>
          </div>
          <em>进入</em>
        </RouterLink>
      </div>

      <div class="workspace-shell">
        <AgentWorkspacePanel
          :company-code="currentCompany?.company_code ? String(currentCompany.company_code) : null"
          :company-name="currentCompany?.company_name"
          :seed-question="seedQuestion"
          title=""
          eyebrow=""
          placeholder="请输入问题，例如：这家企业当前最值得关注的经营风险是什么？"
        />
      </div>
    </section>

    <aside class="intel-rail">
      <article class="panel-card intel-card">
        <div class="panel-head compact">
          <div>
            <p class="section-tag">系统可信度</p>
            <h3>能力底座</h3>
          </div>
          <RouterLink to="/quality" class="text-link-button">查看治理</RouterLink>
        </div>
        <div class="capability-list">
          <div v-for="item in aiPillarHighlights" :key="item.name" class="capability-item">
            <div class="trace-title-row"><strong>{{ item.name }}</strong><span>{{ item.score }}</span></div>
            <p>{{ item.summary }}</p>
          </div>
          <div class="capability-meta">
            <span>模型效果</span>
            <strong>AUC {{ riskAucText }}</strong>
          </div>
        </div>
      </article>

      <article class="panel-card intel-card">
        <div class="panel-head compact">
          <div>
            <p class="section-tag">数据时效</p>
            <h3>可信状态</h3>
          </div>
        </div>
        <div class="mini-grid triple">
          <div class="mini-card"><span>官方覆盖</span><strong>{{ qualityCoverageText }}</strong></div>
          <div class="mini-card"><span>图表补全</span><strong>{{ multimodalCoverageText }}</strong></div>
          <div class="mini-card"><span>待复核</span><strong>{{ pendingReviewText }}</strong></div>
        </div>
      </article>
    </aside>

    <section class="lower-grid">
      <article class="panel-card lower-panel">
        <div class="panel-head compact">
          <div>
            <p class="section-tag">企业态势</p>
            <h3>经营与风险矩阵</h3>
          </div>
          <span class="badge-subtle">点击企业进入详情</span>
        </div>
        <EChartPanel :option="companyMatrixOption" height="360px" @chart-click="handleCompanyMatrixClick" />
      </article>

      <div class="side-stack">
        <article class="panel-card lower-panel">
          <div class="panel-head compact"><div><p class="section-tag">行业热度</p><h3>研报主线</h3></div></div>
          <button v-for="item in industryHeatRows" :key="String(item.industry_name)" type="button" class="signal-item" @click="primeAgentPrompt(buildIndustryPrompt(String(item.industry_name || '')), 'industry_trend')">
            <div class="signal-head"><strong>{{ formatIndustry(String(item.industry_name || '')) }}</strong><span>{{ item.report_count }} 篇</span></div>
            <div class="signal-bar"><i :style="{ width: heatWidth(item.report_count, industryHeatMax) }"></i></div>
          </button>
        </article>

        <article class="panel-card lower-panel">
          <div class="panel-head compact"><div><p class="section-tag">宏观脉冲</p><h3>外部变量</h3></div></div>
          <button v-for="item in macroRows" :key="String(item.indicator_name || item.period || 'macro')" type="button" class="macro-item" @click="primeAgentPrompt(buildMacroPrompt(item), 'company_decision_brief')">
            <span>{{ String(item.indicator_name || '宏观指标') }}</span>
            <strong>{{ formatMacroValue(item.indicator_value, item.unit) }}</strong>
            <p>最新周期 {{ String(item.period || macroFreshnessText) }}</p>
          </button>
        </article>
      </div>
    </section>
    </template>
    <section v-else class="panel-card overview-loading-shell">
      <div class="overview-loading-head">
        <p class="section-tag">企业运营分析中枢</p>
        <h1>正在准备分析现场</h1>
        <p>系统正在同步企业池、数据时效和能力状态。</p>
      </div>
      <div class="overview-loading-grid">
        <div class="overview-loading-card large"></div>
        <div class="overview-loading-card"></div>
        <div class="overview-loading-card"></div>
      </div>
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

const taskModeLabels: Record<string, string> = { company_diagnosis: '企业诊断', company_risk_forecast: '风险预警', company_decision_brief: '决策建议', industry_trend: '行业趋势', data_quality: '数据治理' };
const exchangeLabels: Record<string, string> = { SSE: '上交所', SZSE: '深交所', BSE: '北交所' };

const store = useDashboardStore();
const agentStore = useAgentThreadStore();
const router = useRouter();
const selectedCode = ref('');
const seedQuestionOverride = ref('');
const aiStackSummary = ref<AIStackSummaryResponse | null>(null);
const qualitySummary = ref<QualitySummaryResponse | null>(null);
const riskModelSummary = ref<RiskModelSummaryResponse | null>(null);
const warehouseOverview = ref<WarehouseOverviewResponse | null>(null);

const rankingRows = computed(() => ((store.payload?.ranking || []) as Array<Record<string, unknown>>).slice(0, 5));
const watchlistRows = computed(() => ((store.payload?.watchlist || []) as Array<Record<string, unknown>>).slice(0, 5));
const macroRows = computed(() => ((store.payload?.macro || []) as Array<Record<string, unknown>>).slice(0, 4));
const industryHeatRows = computed(() => (warehouseOverview.value?.industry_heat?.slice(0, 5) || []) as Array<Record<string, unknown>>);
const industryHeatMax = computed(() => Math.max(...industryHeatRows.value.map((item) => Number(item.report_count || 0)), 1));
const currentCompany = computed(() => store.targets.find((item) => String(item.company_code) === selectedCode.value) || null);
const currentRanking = computed(() => rankingRows.value.find((item) => String(item.company_code) === selectedCode.value) || null);
const currentTaskLabel = computed(() => taskModeLabels[agentStore.taskMode || 'company_diagnosis'] || '企业诊断');
const currentRiskText = computed(() => currentRanking.value ? `${String(currentRanking.value.risk_level || '待定')}风险` : '待分析');
const currentScoreText = computed(() => currentRanking.value ? scoreText(currentRanking.value.total_score) : '待分析');
const comparePeerCode = computed(() => {
  const leaderCode = rankingRows.value[0]?.company_code ? String(rankingRows.value[0].company_code) : '';
  if (!selectedCode.value) return leaderCode;
  if (leaderCode && leaderCode !== selectedCode.value) return leaderCode;
  const peer = rankingRows.value.find((item) => String(item.company_code) !== selectedCode.value)?.company_code;
  return String(peer || leaderCode);
});
const cockpitRoutes = computed(() => [
  { tag: '详情', title: '企业工作台', body: '进入企业详情页，看经营、风险与证据回链。', to: selectedCode.value ? `/workbench/${selectedCode.value}` : '/workbench' },
  { tag: '对比', title: '横向判断', body: '和当前高分同行做直接对照，判断谁更强。', to: { path: '/compare', query: selectedCode.value && comparePeerCode.value ? { companies: `${selectedCode.value},${comparePeerCode.value}` } : {} } },
  { tag: '导出', title: '分析材料', body: '导出当前企业的结构化分析材料和证据包。', to: selectedCode.value ? `/competition/${selectedCode.value}` : '/competition' },
  { tag: '治理', title: '数据可信', body: '查看真实披露、图表补全和治理缺口。', to: '/quality' },
]);
const interactionScenes = computed(() => {
  const companyName = currentCompany.value?.company_name || '当前企业';
  return [
    { label: '管理层晨会', title: '先看经营动作', prompt: `如果今天开经营会，${companyName}最该先讨论什么？`, taskMode: 'company_decision_brief' },
    { label: '投研快览', title: '先看横向差异', prompt: `把${companyName}和当前高分同行放在一起，先看最关键的差异。`, taskMode: 'company_diagnosis' },
    { label: '风控巡检', title: '先看风险与缺口', prompt: `从风险和数据可信度两个角度，判断${companyName}当前最该盯的信号。`, taskMode: 'company_risk_forecast' },
  ];
});
const seedQuestion = computed(() => seedQuestionOverride.value || (currentCompany.value ? `${currentCompany.value.company_name}当前最值得关注的经营问题是什么？` : '当前最值得关注的经营问题是什么？'));
const dashboardFreshness = computed(() => store.payload?.freshness || null);
const dashboardMetrics = computed(() => store.payload?.metrics || null);
const annualReportText = computed(() => dashboardFreshness.value?.annual_report_year ? `${dashboardFreshness.value.annual_report_year} 年报` : '待刷新');
const annualPublishText = computed(() => dashboardFreshness.value?.annual_report_published_at ? `披露日 ${formatDate(dashboardFreshness.value.annual_report_published_at)}` : '尚未识别到官方年报时间');
const latestOfficialText = computed(() => dashboardFreshness.value?.latest_official_disclosure ? `${dashboardFreshness.value.latest_periodic_label || '定期报告'}更新到 ${formatDate(dashboardFreshness.value.latest_official_disclosure)}` : '官方披露待更新');
const researchFreshnessText = computed(() => formatDate(dashboardFreshness.value?.latest_research_report));
const industryFreshnessText = computed(() => formatDate(dashboardFreshness.value?.latest_industry_report));
const macroFreshnessText = computed(() => dashboardFreshness.value?.latest_macro_period || '待刷新');
const evidenceVolumeText = computed(() => dashboardMetrics.value ? `${Number(dashboardMetrics.value.research_report_count || 0) + Number(dashboardMetrics.value.industry_report_count || 0)} 份` : '待刷新');
const pillarNameMap: Record<string, string> = {
  '传统应用 + Agent': '智能体工作流',
  '深度学习 / 大模型': '模型能力',
  '大数据 / 计算引擎': '数据底座',
};
const aiPillarHighlights = computed(() => (aiStackSummary.value?.pillars || []).slice(0, 3).map((item) => ({ name: pillarNameMap[item.name] || item.name, score: `${Math.round((item.readiness_score || 0) * 100)}`, summary: item.summary })));
const riskAucText = computed(() => riskModelSummary.value?.metrics?.roc_auc?.toFixed(3) || '暂无');
const qualityCoverageText = computed(() => qualitySummary.value ? `${Math.round((qualitySummary.value.official_report_coverage_ratio || 0) * 100)}%` : '加载中');
const multimodalCoverageText = computed(() => qualitySummary.value ? `${Math.round((qualitySummary.value.multimodal_extract_coverage_ratio || 0) * 100)}%` : '加载中');
const pendingReviewText = computed(() => qualitySummary.value ? `${qualitySummary.value.pending_review_count} 项` : '加载中');
const isReady = computed(() => Boolean(
  selectedCode.value &&
  store.targets.length &&
  !store.loading &&
  aiStackSummary.value &&
  qualitySummary.value &&
  riskModelSummary.value &&
  warehouseOverview.value
));

const companyMatrixOption = computed(() => {
  const scatterData = rankingRows.value.map((item) => ({ value: [Number(item.total_score || 0), { 低: 0, 中: 1, 高: 2 }[String(item.risk_level)] ?? 1, 16], name: item.company_name, companyCode: item.company_code, riskLevel: item.risk_level }));
  return { backgroundColor: 'transparent', tooltip: { trigger: 'item', formatter: (params: { data?: { name?: string; riskLevel?: string; value?: [number, number, number] } }) => `${params.data?.name}<br/>综合分：${params.data?.value?.[0]}<br/>风险：${params.data?.riskLevel}` }, grid: { left: 46, right: 16, top: 30, bottom: 38 }, xAxis: { name: '综合得分', nameTextStyle: { color: '#527496' }, axisLabel: { color: '#6f8cab' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.12)' } }, axisLine: { lineStyle: { color: 'rgba(148,163,184,0.22)' } } }, yAxis: { name: '风险等级', nameTextStyle: { color: '#527496' }, min: -0.3, max: 2.3, interval: 1, axisLabel: { color: '#6f8cab', formatter: (value: number) => ['低', '中', '高'][value] || '' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.12)' } }, axisLine: { lineStyle: { color: 'rgba(148,163,184,0.22)' } } }, series: [{ type: 'scatter', data: scatterData, symbolSize: 28, label: { show: true, formatter: (params: { data?: { name?: string } }) => params.data?.name || '', color: '#0e1726', fontSize: 12, position: 'top' }, itemStyle: { color: '#20466f', shadowBlur: 14, shadowColor: 'rgba(32,70,111,0.2)', borderColor: 'rgba(255,255,255,0.88)', borderWidth: 1 } }] } as const;
});

function formatIndustry(value?: string | null) { return value ? value.replace('Ⅱ', '').replace('I', '').replace('Ⅲ', '').trim() : '未分类'; }
function formatExchange(value?: string | null) { return exchangeLabels[String(value || '').toUpperCase()] || String(value || '未标注'); }
function scoreText(value: unknown) { const num = typeof value === 'number' ? value : Number(value || 0); return `${num.toFixed(1)} 分`; }
function formatDate(value?: string | null) { return value ? String(value).replace('T', ' ').slice(0, 10) : '待刷新'; }
function formatMacroValue(value: unknown, unit?: unknown) { const num = typeof value === 'number' ? value : Number(value); return Number.isFinite(num) ? `${num}${typeof unit === 'string' ? unit : ''}` : '待刷新'; }
function getRiskFlagsText(flags?: unknown) { return Array.isArray(flags) && flags.length ? flags.slice(0, 2).join('；') : '暂未发现显著风险信号'; }
function heatWidth(value: unknown, max: number) { return `${Math.max(12, (Number(value || 0) / Math.max(max, 1)) * 100)}%`; }
function buildIndustryPrompt(industryName?: unknown) { return `结合${formatIndustry(String(industryName || '当前赛道'))}赛道的最新研报热度，判断${currentCompany.value?.company_name || '当前企业'}接下来最需要盯的行业变量与机会风险。`; }
function buildMacroPrompt(item: Record<string, unknown>) { return `宏观指标“${String(item.indicator_name || '宏观指标')}”对${currentCompany.value?.company_name || '当前企业'}接下来的经营判断和动作建议有什么影响？`; }
function focusAgentStage() { document.querySelector('.command-stage')?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
function primeAgentPrompt(question: string, taskMode: string) { seedQuestionOverride.value = question; agentStore.setTaskMode(taskMode); focusAgentStage(); }
function activateInteractionScene(item: { prompt: string; taskMode: string }) { primeAgentPrompt(item.prompt, item.taskMode); }
function handleCompanyMatrixClick(params: Record<string, unknown>) { const data = params.data as { companyCode?: string } | undefined; if (data?.companyCode) void router.push(`/workbench/${data.companyCode}`); }

watch(selectedCode, (value, previous) => {
  const company = store.targets.find((item) => String(item.company_code) === value);
  if (!company) return;
  const companyCode = String(company.company_code);
  const keepThread = Boolean(agentStore.threadId) && previous === '' && agentStore.focusCompanyCode === companyCode;
  if (value !== previous) seedQuestionOverride.value = '';
  agentStore.setFocus(companyCode, company.company_name);
  if (value !== previous && !keepThread) agentStore.resetThread(companyCode, company.company_name);
});

onMounted(async () => {
  if (!store.payload && !store.loading) await store.load();
  if (!selectedCode.value && store.targets.length) {
    const existingFocus = agentStore.focusCompanyCode ? String(agentStore.focusCompanyCode) : '';
    selectedCode.value = store.targets.some((item) => String(item.company_code) === existingFocus) ? existingFocus : String(store.targets[0].company_code);
  }
  const [stack, quality, riskSummary, warehouse] = await Promise.all([api.getAIStack(), api.getQualitySummary(), api.getRiskModelSummary(), api.getWarehouseOverview(8)]);
  aiStackSummary.value = stack;
  qualitySummary.value = quality;
  riskModelSummary.value = riskSummary;
  warehouseOverview.value = warehouse;
});
</script>

<style scoped>
.overview-shell{display:grid;grid-template-columns:300px minmax(0,1fr) 340px;gap:18px;align-items:start}.panel-card,.command-stage{border-radius:28px;border:1px solid rgba(135,156,184,.18);box-shadow:var(--shadow-md)}.panel-card{padding:22px;background:rgba(255,255,255,.86);backdrop-filter:blur(16px)}.focus-rail,.intel-rail,.side-stack{display:grid;gap:18px}.focus-rail,.intel-rail{position:sticky;top:92px}.command-stage{display:grid;gap:18px;padding:24px;background:radial-gradient(circle at top right,rgba(242,163,74,.18),transparent 24%),radial-gradient(circle at 12% 12%,rgba(76,121,190,.24),transparent 22%),linear-gradient(180deg,rgba(9,22,41,.98),rgba(14,28,52,.96));color:#eef5ff}.overview-loading-shell{grid-column:1 / -1;display:grid;gap:22px;min-height:520px;align-content:start;padding:28px;background:radial-gradient(circle at top right,rgba(242,163,74,.12),transparent 24%),linear-gradient(180deg,#fdfefe,#f3f7fc)}.overview-loading-head h1,.overview-loading-head p{margin:0}.overview-loading-head h1{margin-top:8px;font-size:clamp(2rem,4vw,3.4rem);line-height:1.04;color:var(--brand-primary)}.overview-loading-head p{margin-top:10px;color:var(--text-secondary)}.overview-loading-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:16px}.overview-loading-card{min-height:240px;border-radius:24px;background:linear-gradient(90deg,rgba(12,27,51,.05),rgba(12,27,51,.12),rgba(12,27,51,.05));background-size:200% 100%;animation:overviewShimmer 1.2s linear infinite}.overview-loading-card.large{min-height:340px}@keyframes overviewShimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}.panel-head,.signal-head,.trace-title-row{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.compact h3,.panel-head h2{margin:4px 0 0}.score-pill,.soft-pill,.mini-card strong,.hero-stat strong,.capability-meta strong{font-family:var(--font-mono)}.score-pill{display:inline-flex;align-items:center;justify-content:center;min-width:86px;min-height:44px;padding:0 16px;border-radius:999px;background:linear-gradient(135deg,rgba(12,27,51,.96),rgba(32,70,111,.92));color:#fff7ee}.field-block{display:grid;gap:8px;margin-top:18px}.focus-select{width:100%;min-height:52px;padding:0 16px;border-radius:16px;border:1px solid rgba(120,142,168,.28);background:rgba(248,251,255,.96)}.pill-row,.scene-grid,.route-grid,.mini-grid{display:grid;gap:12px}.pill-row{display:flex;flex-wrap:wrap;margin-top:16px}.soft-pill{padding:7px 12px;border-radius:999px;background:rgba(14,23,38,.06);color:var(--brand-secondary);font-size:12px;font-weight:700}.mini-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.mini-grid.triple{grid-template-columns:repeat(3,minmax(0,1fr))}.mini-card,.hero-stat,.capability-item,.capability-meta{display:grid;gap:6px;padding:14px 16px;border-radius:18px}.mini-card,.capability-item,.capability-meta{background:rgba(12,27,51,.04)}.focus-note,.watch-item p,.route-card p,.scene-card p,.hero-copy,.hero-stat p,.capability-item p,.macro-item p{margin:0;color:var(--text-secondary)}.watch-stack{display:grid;gap:12px;margin-top:20px}.watch-item,.route-card{text-decoration:none;color:inherit}.watch-item{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;padding:14px 0;border-top:1px solid rgba(120,142,168,.14)}.watch-item:first-of-type,.signal-item:first-of-type,.macro-item:first-of-type{border-top:none;padding-top:0}.watch-item span{color:var(--brand-warning);font-size:12px;font-weight:700}.hero-panel{display:grid;gap:18px}.hero-panel h1{margin:8px 0 10px;max-width:10ch;font-size:clamp(2.5rem,4vw,4.2rem);line-height:1.02;letter-spacing:-.05em;color:#f6fbff}.hero-copy,.route-card span,.route-card p,.scene-card span,.scene-card p,.hero-stat p{color:rgba(214,230,250,.74)}.hero-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.hero-stat{background:rgba(255,255,255,.06);border:1px solid rgba(149,182,226,.14)}.scene-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.route-grid{grid-template-columns:repeat(4,minmax(0,1fr))}.scene-card,.route-card{transition:transform .18s ease,border-color .18s ease,background .18s ease,box-shadow .18s ease}.scene-card{display:grid;gap:8px;min-height:136px;padding:18px;border-radius:22px;border:1px solid rgba(145,181,227,.14);background:linear-gradient(180deg,rgba(13,29,53,.9),rgba(9,21,40,.86));color:#eef5ff;text-align:left}.route-card{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;min-height:108px;padding:18px;border-radius:20px;border:1px solid rgba(145,181,227,.12);background:rgba(255,255,255,.05);color:#eef5ff}.route-card em{font-style:normal;color:#ffd3a3;white-space:nowrap}.scene-card:hover,.route-card:hover{transform:translateY(-2px);border-color:rgba(242,163,74,.26);box-shadow:0 18px 42px rgba(7,16,30,.22)}.workspace-shell{border-radius:24px;overflow:hidden}.workspace-shell :deep(.agent-workspace-panel){border:1px solid rgba(145,181,227,.12);background:rgba(255,255,255,.98);box-shadow:none}.workspace-shell :deep(.task-mode-toolbar){padding:18px 18px 0}.workspace-shell :deep(.task-mode-pill-group){gap:10px}.workspace-shell :deep(.task-mode-toggle){min-height:42px;border-radius:999px}.workspace-shell :deep(.bottom-input-shell){margin-top:0;border-top:1px solid rgba(120,142,168,.14);border-radius:0}.intel-card,.lower-panel,.capability-list{display:grid;gap:16px}.lower-grid{grid-column:2 / 4;display:grid;grid-template-columns:minmax(0,1.35fr) minmax(360px,.9fr);gap:18px}.signal-item,.macro-item{display:grid;gap:10px;width:100%;padding:14px 0;border:none;border-top:1px solid rgba(120,142,168,.14);background:transparent;text-align:left;color:inherit}.signal-head span{color:var(--text-tertiary)}.signal-bar{height:7px;border-radius:999px;background:rgba(120,142,168,.14);overflow:hidden}.signal-bar i{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,rgba(32,70,111,.9),rgba(242,163,74,.92))}.macro-item strong{font-family:var(--font-mono)}@media (max-width:1480px){.overview-shell{grid-template-columns:280px minmax(0,1fr)}.intel-rail{grid-column:1 / -1;position:static;grid-template-columns:repeat(2,minmax(0,1fr))}.lower-grid{grid-column:1 / -1}}@media (max-width:1180px){.overview-shell,.lower-grid,.overview-loading-grid{grid-template-columns:1fr}.focus-rail,.intel-rail{position:static}.route-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media (max-width:820px){.command-stage,.panel-card,.overview-loading-shell{padding:18px;border-radius:22px}.scene-grid,.route-grid,.mini-grid,.hero-stats,.intel-rail{grid-template-columns:1fr}.hero-panel h1,.overview-loading-head h1{max-width:none;font-size:2.3rem}}
</style>
