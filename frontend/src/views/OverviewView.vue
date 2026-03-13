<template>
  <div class="page-stack overview-clean-page">
    <section class="overview-shell">
      <div class="overview-hero">
        <div class="overview-hero-copy">
          <span class="overview-kicker">真实数据 · Agent · 决策支持</span>
          <h1>企业问答中枢</h1>
          <p>{{ store.homeSummary || '围绕真实财报、研报与宏观数据展开企业分析，不再把所有能力堆在一个页面里。' }}</p>
        </div>

        <div class="overview-hero-actions">
          <label class="overview-company-picker">
            <span>当前企业</span>
            <select v-model="selectedCode" class="v-select-input">
              <option value="" disabled>— 选择目标企业 —</option>
              <option v-for="item in store.targets" :key="item.company_code" :value="String(item.company_code)">
                {{ item.company_name }}
              </option>
            </select>
          </label>
        </div>
      </div>

      <div class="overview-metric-strip" v-if="heroMetrics.length || currentCompany">
        <article v-for="item in heroMetrics" :key="item.label" class="overview-metric-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
        <article v-if="currentCompany" class="overview-metric-card wide">
          <span>当前标的</span>
          <strong>{{ currentCompany.company_name }}</strong>
          <p>{{ formatExchange(currentCompany.exchange) }} · {{ formatIndustry(currentCompany.industry) }}</p>
        </article>
      </div>

      <div class="overview-context-strip" v-if="currentCompany || contextCards.length || store.systemStatusTagline">
        <div class="overview-tag-row" v-if="currentCompany">
          <span class="overview-tag">{{ formatIndustry(currentCompany.industry) }}</span>
          <span v-for="tag in currentTags" :key="tag" class="overview-tag accent">{{ tag }}</span>
        </div>
        <div class="overview-inline-metrics" v-if="contextCards.length">
          <span v-for="item in contextCards" :key="item.label" class="overview-inline-chip">
            {{ item.label }} · {{ item.value }}
          </span>
        </div>
        <p v-if="store.systemStatusTagline" class="overview-status-text">{{ store.systemStatusTagline }}</p>
      </div>

      <section class="overview-main-panel">
        <AgentWorkspacePanel
          :company-code="currentCompany?.company_code ? String(currentCompany.company_code) : null"
          :company-name="currentCompany?.company_name"
          :seed-question="seedQuestion"
          title=""
          eyebrow=""
          placeholder="输入你的问题，例如：该企业当前最核心的经营风险是什么？"
        />
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import AgentWorkspacePanel from '../components/AgentWorkspacePanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';
import { useDashboardStore } from '../stores/dashboard';

const store = useDashboardStore();
const agentStore = useAgentThreadStore();

const selectedCode = ref('');
const exchangeLabels: Record<string, string> = { SSE: '上交所', SZSE: '深交所', BSE: '北交所' };

const currentCompany = computed(() => store.targets.find((item) => String(item.company_code) === selectedCode.value) || null);
const currentTags = computed(() => currentCompany.value?.tags || []);

const heroMetrics = computed(() => {
  const metrics = store.payload?.metrics;
  const freshness = store.payload?.freshness;
  const cards: Array<{ label: string; value: string }> = [];
  if (metrics) {
    cards.push({ label: '覆盖企业', value: `${metrics.sample_count} 家` });
    cards.push({ label: '证据规模', value: `${metrics.research_report_count + metrics.industry_report_count} 条` });
  }
  if (freshness?.latest_periodic_label) {
    cards.push({ label: '最新披露', value: freshness.latest_periodic_label });
  }
  return cards.slice(0, 3);
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
      detail: '当前行业证据回到最新日期',
    });
  }
  if (metrics) {
    cards.push({
      label: '平均赋分',
      value: metrics.avg_score.toFixed(1),
      detail: '用于观察当前目标池整体经营状态',
    });
  }
  return cards.slice(0, 3);
});

const seedQuestion = computed(() => currentCompany.value ? `${currentCompany.value.company_name}当前最值得关注的经营问题是什么？` : '当前最值得关注的经营问题是什么？');

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
  agentStore.setFocus(companyCode, company.company_name);
  if (value !== previous) {
    agentStore.resetThread(companyCode, company.company_name);
  }
});

onMounted(async () => {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  if (!selectedCode.value && store.targets.length) {
    selectedCode.value = String(store.targets[0].company_code);
  }
});
</script>

<style scoped>
.overview-clean-page,
.overview-shell,
.overview-hero,
.overview-hero-actions,
.overview-metric-strip,
.overview-context-strip,
.overview-tag-row,
.overview-inline-metrics {
  display: grid;
  gap: 18px;
}

.overview-shell,
.overview-main-panel {
  border-radius: 30px;
  border: 1px solid rgba(10, 31, 68, 0.08);
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.08);
}

.overview-shell {
  padding: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 249, 252, 0.98));
}

.overview-hero {
  grid-template-columns: minmax(0, 1fr) minmax(220px, 280px);
  align-items: end;
  padding-bottom: 6px;
  background:
    radial-gradient(circle at top left, rgba(52, 211, 153, 0.14), transparent 24%),
    linear-gradient(180deg, rgba(255, 254, 249, 0.82), rgba(245, 248, 252, 0.82));
}

.overview-kicker,
.overview-hero-actions span,
.overview-metric-card span {
  display: inline-flex;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 700;
  color: #6a7c93;
}

.overview-hero h1 {
  margin: 8px 0 8px;
  font-size: 42px;
}

.overview-hero p {
  margin: 0;
  max-width: 720px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.overview-hero-actions {
  align-items: end;
}

.overview-company-picker {
  display: grid;
  gap: 8px;
}

.overview-metric-strip {
  grid-template-columns: repeat(4, minmax(140px, 1fr));
  gap: 12px;
}

.overview-metric-card {
  min-height: 0;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(10, 31, 68, 0.08);
  background: rgba(255, 255, 255, 0.82);
}

.overview-metric-card strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
  line-height: 1.05;
}

.overview-metric-card p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

.overview-metric-card.wide {
  min-width: 0;
}

.overview-context-strip {
  gap: 12px;
  padding: 0 2px 6px;
}

.overview-tag-row {
  grid-template-columns: repeat(auto-fit, minmax(88px, max-content));
}

.overview-tag {
  padding: 8px 12px;
  border-radius: 999px;
  background: #edf3f9;
  color: #35577f;
  font-size: 12px;
  font-weight: 600;
}

.overview-tag.accent {
  background: #fff0db;
  color: #9b6120;
}

.overview-inline-metrics {
  grid-auto-flow: column;
  justify-content: start;
  gap: 10px;
  overflow-x: auto;
}

.overview-inline-chip {
  display: inline-flex;
  padding: 10px 14px;
  border-radius: 999px;
  background: #f5f8fb;
  border: 1px solid rgba(10, 31, 68, 0.06);
  color: #4b617b;
  font-size: 13px;
  white-space: nowrap;
}

.overview-status-text {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

@media (max-width: 980px) {
  .overview-hero,
  .overview-metric-strip {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .overview-company-picker {
    width: 100%;
  }

  .overview-shell {
    padding: 18px;
  }

  .overview-hero h1 {
    font-size: 34px;
  }
}
</style>
