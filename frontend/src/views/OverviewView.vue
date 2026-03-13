<template>
  <div class="page-stack overview-page v-asymmetric-layout">
    
    <!-- Left: Massive Typography & Agent Interaction -->
    <section class="v-main-stage">
      <div class="v-hero-header">
        <div class="v-hero-kicker">真实数据 · Agent · 决策支持</div>
        <div class="v-title-lockup">
          <h1 class="v-mega-title">
            <span class="v-title-primary">企业分析</span>
            <span class="v-title-accent">中枢</span>
          </h1>
          <p class="v-title-note">把真实财报、研报和模型判断收束到一个决策入口。</p>
        </div>
        <p class="v-hero-subtitle">
          {{ store.homeSummary || '围绕真实财报、研报与宏观数据展开经营分析、对比判断与风险穿透。' }}
        </p>
      </div>

      <div class="v-workspace-wrapper">
        <AgentWorkspacePanel
          :company-code="currentCompany?.company_code ? String(currentCompany.company_code) : null"
          :company-name="currentCompany?.company_name"
          :seed-question="seedQuestion"
          title=""
          eyebrow=""
          placeholder="输入任何问题... 例如：该企业当前最核心的经营风险是什么？"
        />
      </div>

      <div class="v-system-status" v-if="store.systemStatusTagline">
        <div class="v-status-dot"></div>
        <span>{{ store.systemStatusTagline }}</span>
      </div>

      <div v-if="signalCards.length" class="v-pulse-strip">
        <article v-for="item in signalCards" :key="item.label" class="v-pulse-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.detail }}</p>
        </article>
      </div>
    </section>

    <!-- Right: Sticky Context & Actions -->
    <aside class="v-side-context">
      <div class="v-context-card">
        <h3 class="v-side-headline">分析标的</h3>
        <label class="v-console-field">
          <select v-model="selectedCode" class="v-select-input">
            <option value="" disabled>— 选择目标企业 —</option>
            <option v-for="item in store.targets" :key="item.company_code" :value="String(item.company_code)">
              {{ item.company_name }} <span v-if="item.exchange">({{ formatExchange(item.exchange) }})</span>
            </option>
          </select>
        </label>

        <div v-if="currentCompany" class="v-focus-identity">
          <strong>{{ currentCompany.company_name }}</strong>
          <p>
            {{ formatExchange(currentCompany.exchange) }} · {{ formatIndustry(currentCompany.industry) }}
          </p>
        </div>

        <div class="v-focus-tags" v-if="currentCompany">
          <span class="v-tag">{{ formatIndustry(currentCompany.industry) }}</span>
          <span class="v-tag highlight" v-for="tag in currentTags" :key="tag">{{ tag }}</span>
        </div>

        <p v-if="currentCompany" class="v-context-note">
          当前问题会默认围绕 {{ currentCompany.company_name }} 展开，适合直接进入企业分析、对比判断或导出材料。
        </p>
      </div>

      <div class="v-action-grid" v-if="currentCompany">
        <div class="v-side-section-label">下一步</div>
        <RouterLink
          v-for="item in cockpitRoutes"
          :key="item.title"
          :to="item.to"
          class="v-action-card"
        >
          <div class="v-action-text">
            <strong>{{ item.title }}</strong>
            <p>{{ item.body }}</p>
          </div>
          <div class="v-action-arrow">→</div>
        </RouterLink>
      </div>

      <div v-if="contextCards.length" class="v-context-data-grid">
        <article v-for="item in contextCards" :key="item.label" class="v-context-data-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.detail }}</p>
        </article>
      </div>

      <div class="v-loading-state" v-if="!isReady">
        <p>正在准备企业列表与当前分析上下文...</p>
      </div>
    </aside>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink } from 'vue-router';
import AgentWorkspacePanel from '../components/AgentWorkspacePanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';
import { useDashboardStore } from '../stores/dashboard';

const store = useDashboardStore();
const agentStore = useAgentThreadStore();

const selectedCode = ref('');
const seedQuestionOverride = ref('');

const exchangeLabels: Record<string, string> = { SSE: '上交所', SZSE: '深交所', BSE: '北交所' };

const currentCompany = computed(() => store.targets.find((item) => String(item.company_code) === selectedCode.value) || null);

// Use pre-computed tags from backend if available
const currentTags = computed(() => {
  if (currentCompany.value?.tags && currentCompany.value.tags.length > 0) {
    return currentCompany.value.tags;
  }
  return [];
});

const isReady = computed(() => !store.loading && store.payload !== null);
const signalCards = computed(() => {
  const metrics = store.payload?.metrics;
  const freshness = store.payload?.freshness;
  const cards: Array<{ label: string; value: string; detail: string }> = [];
  if (metrics) {
    cards.push(
      {
        label: '覆盖企业',
        value: `${metrics.sample_count} 家`,
        detail: '当前已进入企业分析池的目标范围。',
      },
      {
        label: '证据规模',
        value: `${metrics.research_report_count + metrics.industry_report_count} 条`,
        detail: '由个股研报和行业研究共同组成。',
      },
      {
        label: '领先标的',
        value: metrics.leader_name,
        detail: `当前综合赋分 ${metrics.leader_score.toFixed(1)}。`,
      },
    );
  }
  if (freshness) {
    cards.push({
      label: '最新披露',
      value: freshness.latest_periodic_label || '年报口径',
      detail: freshness.latest_official_disclosure || '披露日期同步中',
    });
  }
  return cards.slice(0, 4);
});

const contextCards = computed(() => {
  const metrics = store.payload?.metrics;
  const freshness = store.payload?.freshness;
  const cards: Array<{ label: string; value: string; detail: string }> = [];
  if (freshness?.annual_report_year) {
    cards.push({
      label: '完整年报',
      value: `${freshness.annual_report_year} 年`,
      detail: freshness.annual_report_published_at || '当前完整财报口径',
    });
  }
  if (freshness?.latest_industry_report) {
    cards.push({
      label: '行业研报',
      value: freshness.latest_industry_report,
      detail: '当前行业证据已同步到最新日期。',
    });
  }
  if (metrics) {
    cards.push({
      label: '平均赋分',
      value: metrics.avg_score.toFixed(1),
      detail: '用于观察当前目标池整体经营状态。',
    });
  }
  return cards.slice(0, 3);
});

const currentRouteQuery = computed(() => {
  if (!selectedCode.value || !currentCompany.value) return {};
  return {
    entry: 'overview',
    focus: selectedCode.value,
    company: currentCompany.value.company_name,
  };
});

const cockpitRoutes = computed(() => [
  {
    title: '决策态势屏',
    body: '面向展示与集中研判的可视化总览界面。',
    to: '/board'
  },
  {
    title: '项目总控台',
    body: '查看数据、Agent、模型、计算与正式交付五条主任务线。',
    to: '/mission-control'
  },
  { 
    title: '企业分析工作台', 
    body: '带有证据链路的单体深度体检。', 
    to: selectedCode.value ? { path: `/workbench/${selectedCode.value}`, query: currentRouteQuery.value } : '/workbench' 
  },
  { 
    title: '企业对比判断', 
    body: '围绕经营、风险与证据差异做横向比较。', 
    to: { path: '/compare', query: selectedCode.value ? { ...currentRouteQuery.value, companies: selectedCode.value } : {} } 
  },
  { 
    title: '导出分析材料', 
    body: '把当前结论整理成正式材料与证据清单。', 
    to: selectedCode.value ? { path: `/competition/${selectedCode.value}`, query: currentRouteQuery.value } : '/competition' 
  },
  { 
    title: '数据可信中心', 
    body: '查看来源、覆盖、时效与质量治理状态。', 
    to: '/quality' 
  },
]);

const seedQuestion = computed(() => seedQuestionOverride.value || (currentCompany.value ? `${currentCompany.value.company_name}当前最值得关注的经营问题是什么？` : '当前最值得关注的经营问题是什么？'));

function formatExchange(value?: string | null) { 
  return exchangeLabels[String(value || '').toUpperCase()] || String(value || '交易所待标注'); 
}

function formatIndustry(value?: string | null) { 
  return value ? value.replace('Ⅱ', '').replace('I', '').replace('Ⅲ', '').trim() : '行业待标注'; 
}

watch(selectedCode, (value, previous) => {
  const company = store.targets.find((item) => String(item.company_code) === value);
  if (!company) return;
  const companyCode = String(company.company_code);
  const keepThread = Boolean(agentStore.threadId) && previous === '' && agentStore.focusCompanyCode === companyCode;
  
  if (value !== previous) seedQuestionOverride.value = '';
  
  agentStore.setFocus(companyCode, company.company_name);
  if (value !== previous && !keepThread) {
    agentStore.resetThread(companyCode, company.company_name);
  }
});

onMounted(async () => {
  if (!store.payload && !store.loading) await store.load();
  if (!selectedCode.value && store.targets.length) {
    const existingFocus = agentStore.focusCompanyCode ? String(agentStore.focusCompanyCode) : '';
    selectedCode.value = store.targets.some((item) => String(item.company_code) === existingFocus) 
      ? existingFocus 
      : String(store.targets[0].company_code);
  }
});
</script>

<style scoped>
.v-asymmetric-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(320px, 0.8fr);
  gap: 6vw;
  align-items: start;
  max-width: 1600px;
  margin: 0 auto;
  padding: 40px 0;
  min-height: 80vh;
  position: relative;
}

/* Left side */
.v-main-stage {
  display: grid;
  gap: 44px;
  position: relative;
  padding: 40px;
  border-radius: 40px;
  background:
    radial-gradient(circle at top left, rgba(57, 255, 20, 0.08), transparent 24%),
    radial-gradient(circle at 82% 16%, rgba(15, 23, 42, 0.09), transparent 26%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 250, 252, 0.98));
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 28px 80px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.v-main-stage::before {
  content: '';
  position: absolute;
  inset: 18px;
  border-radius: 28px;
  border: 1px solid rgba(15, 23, 42, 0.05);
  pointer-events: none;
}

.v-hero-header {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 20px;
}

.v-hero-kicker {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.8);
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.v-title-lockup {
  display: grid;
  gap: 16px;
}

.v-mega-title {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 14px 18px;
  font-family: 'Syne', 'DM Sans', sans-serif;
  font-size: clamp(46px, 5.3vw, 76px);
  font-weight: 800;
  line-height: 0.98;
  letter-spacing: -0.04em;
  margin: 0;
  color: var(--text-primary);
}

.v-title-primary {
  display: inline-block;
}

.v-title-accent {
  display: inline-flex;
  align-items: center;
  padding: 10px 18px 12px;
  border-radius: 24px;
  background: linear-gradient(135deg, #0f172a, #111827);
  color: #ffffff;
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.14);
}

.v-title-note {
  margin: 0;
  max-width: 520px;
  font-size: 14px;
  line-height: 1.7;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-hero-subtitle {
  font-size: 18px;
  color: var(--text-secondary);
  max-width: 560px;
  line-height: 1.7;
  margin: 0;
}

.v-workspace-wrapper {
  position: relative;
  z-index: 2;
}

.v-system-status {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: var(--bg-surface-highlight);
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  width: fit-content;
}

.v-pulse-strip {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.v-pulse-card {
  display: grid;
  gap: 8px;
  min-height: 148px;
  padding: 18px 18px 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(15, 23, 42, 0.07);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.06);
}

.v-pulse-card span {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
  font-weight: 700;
}

.v-pulse-card strong {
  font-family: 'Syne', 'DM Sans', sans-serif;
  font-size: clamp(24px, 2.2vw, 34px);
  line-height: 1.08;
  color: var(--text-primary);
}

.v-pulse-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.v-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--brand-primary);
  box-shadow: 0 0 8px var(--brand-primary);
}

/* Right side */
.v-side-context {
  position: sticky;
  top: 100px;
  display: grid;
  gap: 24px;
}

.v-context-card {
  padding: 24px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  box-shadow: var(--shadow-sm);
}

.v-side-headline {
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-tertiary);
  margin: 0 0 16px;
  font-weight: 600;
}

.v-console-field {
  display: block;
}

.v-select-input {
  width: 100%;
  padding: 12px 14px;
  border-radius: 6px;
  border: 1px solid var(--border-strong);
  background: var(--bg-base);
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s;
  appearance: none;
  background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23333%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E');
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 16px;
}

.v-select-input:hover {
  border-color: var(--text-primary);
}

.v-focus-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.v-focus-identity {
  margin-top: 16px;
  padding: 16px 18px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
  background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,248,250,0.98) 100%);
}

.v-focus-identity strong {
  display: block;
  font-size: 22px;
  line-height: 1.15;
  color: var(--text-primary);
}

.v-focus-identity p {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.v-tag {
  padding: 4px 10px;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.v-tag.highlight {
  background: var(--bg-surface-highlight);
  color: var(--text-primary);
  border-color: var(--border-strong);
}

.v-context-note {
  margin: 16px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.v-action-grid {
  display: grid;
  gap: 12px;
}

.v-context-data-grid {
  display: grid;
  gap: 12px;
}

.v-context-data-card {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(15, 23, 42, 0.07);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.05);
}

.v-context-data-card span {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-context-data-card strong {
  font-size: 24px;
  line-height: 1.1;
  color: var(--text-primary);
}

.v-context-data-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.v-side-section-label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-tertiary);
  padding: 2px 2px 0;
}

.v-action-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  padding: 20px;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  color: var(--text-primary);
  text-decoration: none;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: var(--shadow-sm);
}

.v-action-card:hover {
  transform: translateY(-2px);
  border-color: var(--text-primary);
  box-shadow: var(--shadow-md);
}

.v-action-text strong {
  display: block;
  font-size: 15px;
  font-family: 'Syne', sans-serif;
  margin-bottom: 6px;
  font-weight: 700;
}

.v-action-text p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.65;
}

.v-action-arrow {
  font-size: 18px;
  color: var(--text-tertiary);
  transition: transform 0.2s;
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.78);
}

.v-action-card:hover .v-action-arrow {
  transform: translateX(4px);
  color: var(--text-primary);
}

.v-loading-state {
  padding: 24px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  font-weight: 600;
  border: 1px dashed var(--border-subtle);
  border-radius: 8px;
}

@media (max-width: 1024px) {
  .v-asymmetric-layout {
    grid-template-columns: 1fr;
    gap: 40px;
  }
  .v-side-context {
    position: static;
  }

  .v-pulse-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .v-main-stage {
    padding: 24px;
    border-radius: 28px;
  }

  .v-mega-title {
    font-size: clamp(38px, 10vw, 56px);
    gap: 10px 12px;
  }

  .v-title-accent {
    padding: 8px 14px 10px;
    border-radius: 20px;
  }

  .v-pulse-strip {
    grid-template-columns: 1fr;
  }
}
</style>
