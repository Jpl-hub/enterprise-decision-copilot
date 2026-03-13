<template>
  <div class="page-stack v-document-page">
    <div class="v-doc-container v-compare-container">
      
      <!-- Top Nav -->
      <nav class="v-doc-nav">
        <RouterLink to="/" class="v-back-link">
          <span class="v-arrow">←</span> <span>返回中枢</span>
        </RouterLink>
        <div v-if="result" class="v-nav-actions">
          <span class="v-nav-actions-label">页面动作</span>
          <div class="v-nav-action-cluster">
            <button v-if="evidenceCompanies.length" class="v-btn-outline" @click="scrollToSection('compare-signal-section')">查看对比信号</button>
            <button v-if="companies.length === 2" class="v-btn-outline" @click="scrollToSection('compare-matrix-section')">查看核心矩阵</button>
            <RouterLink :to="`/workbench/${result.winner_company_code}`" class="v-btn-solid">进入优势方分析</RouterLink>
            <RouterLink :to="`/competition/${result.winner_company_code}`" class="v-btn-outline">导出优势方材料</RouterLink>
          </div>
        </div>
      </nav>

      <!-- Strategy Header -->
      <header class="v-doc-header">
        <h1 class="v-doc-title">企业对比判断</h1>
        <p class="v-doc-subtitle">基于财务口径、研究证据与财报图表锚点，对两家企业做横向判断与证据回链。</p>
      </header>

      <div v-if="fromOverview" class="v-entry-note">
        <span class="v-entry-note-label">来自分析中枢</span>
        <p>已承接首页中的关注企业与问题语境，适合直接完成横向比较并继续进入优势方分析。</p>
      </div>

      <!-- Selection Stage -->
      <section class="v-config-stage">
        <h2 class="v-section-title">01 / 选择对比对象</h2>
        <div class="v-target-grid">
          <button
            v-for="item in targets"
            :key="item.company_code"
            class="v-target-btn"
            :class="{ 'is-selected': selectedCodes.includes(item.company_code) }"
            @click="toggleCompany(item.company_code)"
          >
            <strong>{{ item.company_name }}</strong>
            <span class="v-exchange-tag">{{ formatExchange(item.exchange) }}</span>
          </button>
        </div>
        <div class="v-action-row">
          <button class="v-btn-solid" @click="loadComparison" :disabled="selectedCodes.length < 2 || isLoading">
            {{ isLoading ? '正在生成横向判断...' : '生成企业对比结果' }}
          </button>
          <button class="v-btn-outline" @click="resetSelection">重置目标</button>
        </div>
        <p class="v-status-note" v-if="selectedCodes.length < 2">至少选择两家企业后，再开始横向比较。</p>
      </section>

      <!-- Loading / Error -->
      <div v-if="isLoading" class="v-loading-block">
        <div class="v-spinner"></div>
        <p>正在整理差异、证据与横向判断...</p>
      </div>
      <div v-if="loadError" class="v-error-block">
        <p><strong>企业对比暂时未能完成</strong></p>
        <p>{{ loadError }}</p>
      </div>

      <!-- Result Stage -->
      <article v-if="!isLoading && result && companies.length === 2" class="v-doc-body">
        
        <!-- Total Verdict -->
        <section class="v-doc-section">
          <h2 class="v-section-title">02 / 全局判断</h2>
          <div class="v-verdict-banner">
            <span class="v-verdict-label">当前相对占优方</span>
            <h3 class="v-verdict-winner">{{ result.winner_company_name }}</h3>
            <p class="v-verdict-summary">{{ result.summary }}</p>
          </div>
          <ul class="v-bullet-list v-judgement-list">
            <li v-for="(hl, idx) in result.highlights" :key="idx">{{ hl }}</li>
          </ul>
        </section>

        <section id="compare-signal-section" class="v-doc-section" v-if="evidenceCompanies.length">
          <h2 class="v-section-title">03 / 对比信号</h2>
          <div class="v-company-brief-grid">
            <article v-for="company in evidenceCompanies" :key="company.company_code" class="v-company-brief-card">
              <div class="v-company-brief-head">
                <div>
                  <strong>{{ company.company_name }}</strong>
                  <p>{{ company.company_code }}</p>
                </div>
                <span class="v-badge" v-if="company.freshness_digest?.latest_periodic_label">
                  {{ company.freshness_digest.latest_periodic_label }}
                </span>
              </div>
              <div class="v-company-brief-metrics">
                <div class="v-company-metric">
                  <span>最新披露</span>
                  <strong>{{ formatDate(company.freshness_digest?.latest_official_disclosure) || '同步中' }}</strong>
                </div>
                <div class="v-company-metric">
                  <span>图表字段</span>
                  <strong>{{ company.multimodal_digest?.filled_field_count || 0 }} 项</strong>
                </div>
                <div class="v-company-metric">
                  <span>个股研报</span>
                  <strong>{{ company.research_digest?.count || 0 }} 篇</strong>
                </div>
                <div class="v-company-metric">
                  <span>行业研报</span>
                  <strong>{{ company.industry_digest?.count || 0 }} 篇</strong>
                </div>
              </div>
              <p class="v-company-brief-copy">
                {{ company.multimodal_digest?.summary || '当前可继续结合财报原件与研报证据完成横向判断。' }}
              </p>
              <div class="v-company-brief-actions">
                <a
                  v-if="company.financial_source_url"
                  class="v-btn-outline"
                  :href="company.financial_source_url"
                  target="_blank"
                  rel="noreferrer"
                >
                  查看财报原件
                </a>
                <RouterLink :to="`/workbench/${company.company_code}`" class="v-btn-solid">
                  进入企业分析
                </RouterLink>
              </div>
            </article>
          </div>
        </section>

        <!-- The Matrix -->
        <section id="compare-matrix-section" class="v-doc-section">
          <h2 class="v-section-title">04 / 核心指标矩阵</h2>
          <div class="v-matrix">
            <div class="v-matrix-header">
              <div class="v-matrix-col-title">对照指标参数</div>
              <div class="v-matrix-col-target"><strong>{{ companies[0].company_name }}</strong></div>
              <div class="v-matrix-col-target"><strong>{{ companies[1].company_name }}</strong></div>
            </div>
            
            <div class="v-matrix-row">
              <div class="v-matrix-label">系统综合赋分</div>
              <div class="v-matrix-val" :class="{ 'v-winning-val': companies[0].total_score > companies[1].total_score }">
                {{ formatNumber(companies[0].total_score, 1) }}
              </div>
              <div class="v-matrix-val" :class="{ 'v-winning-val': companies[1].total_score > companies[0].total_score }">
                {{ formatNumber(companies[1].total_score, 1) }}
              </div>
            </div>

            <div class="v-matrix-row">
              <div class="v-matrix-label">研报覆盖密度</div>
              <div class="v-matrix-val" :class="{ 'v-winning-val': (companies[0].research_report_count) > (companies[1].research_report_count) }">
                {{ companies[0].research_report_count }} 篇
              </div>
              <div class="v-matrix-val" :class="{ 'v-winning-val': (companies[1].research_report_count) > (companies[0].research_report_count) }">
                {{ companies[1].research_report_count }} 篇
              </div>
            </div>

            <div class="v-matrix-row">
              <div class="v-matrix-label">营业收入规模 (百万)</div>
              <div class="v-matrix-val" :class="{ 'v-winning-val': (companies[0].revenue_million) > (companies[1].revenue_million) }">
                {{ formatNumber(companies[0].revenue_million, 0) }}
              </div>
              <div class="v-matrix-val" :class="{ 'v-winning-val': (companies[1].revenue_million) > (companies[0].revenue_million) }">
                {{ formatNumber(companies[1].revenue_million, 0) }}
              </div>
            </div>

            <div class="v-matrix-row">
              <div class="v-matrix-label">净利润规模 (百万)</div>
              <div class="v-matrix-val" :class="{ 'v-winning-val': (companies[0].net_profit_million) > (companies[1].net_profit_million) }">
                {{ formatNumber(companies[0].net_profit_million, 0) }}
              </div>
              <div class="v-matrix-val" :class="{ 'v-winning-val': (companies[1].net_profit_million) > (companies[0].net_profit_million) }">
                {{ formatNumber(companies[1].net_profit_million, 0) }}
              </div>
            </div>

            <div class="v-matrix-row">
              <div class="v-matrix-label">净利率 (净利润占比)</div>
              <div class="v-matrix-val" :class="{ 'v-winning-val': (companies[0].net_margin_pct || 0) > (companies[1].net_margin_pct || 0) }">
                {{ formatPercent(companies[0].net_margin_pct) }}
              </div>
              <div class="v-matrix-val" :class="{ 'v-winning-val': (companies[1].net_margin_pct || 0) > (companies[0].net_margin_pct || 0) }">
                {{ formatPercent(companies[1].net_margin_pct) }}
              </div>
            </div>

            <div class="v-matrix-row">
              <div class="v-matrix-label">风险定级</div>
              <div class="v-matrix-val" :class="{ 'v-risk-val': companies[0].risk_level === '高' }">
                {{ companies[0].risk_level }}风险
              </div>
              <div class="v-matrix-val" :class="{ 'v-risk-val': companies[1].risk_level === '高' }">
                {{ companies[1].risk_level }}风险
              </div>
            </div>

          </div>
        </section>

        <!-- Sector Detail -->
        <section class="v-doc-section" v-if="result.dimensions && result.dimensions.length">
          <h2 class="v-section-title">05 / 维度判断</h2>
          <div class="v-dimension-grid">
            <div v-for="dim in result.dimensions" :key="dim.dimension" class="v-dimension-card">
              <h3 class="v-dimension-title">{{ dim.dimension }}</h3>
              <p class="v-dimension-conclusion">{{ dim.conclusion }}</p>
              <div class="v-dimension-tags">
                <span class="v-badge v-badge-winner">优势方: {{ dim.winner_company_name }}</span>
              </div>
            </div>
          </div>
        </section>

        <section class="v-doc-section v-action-section">
          <h2 class="v-section-title">06 / 后续动作</h2>
          <div class="v-nav-actions bottom-actions">
            <span class="v-nav-actions-label">继续推进</span>
            <div class="v-nav-action-cluster">
              <RouterLink :to="`/workbench/${result.winner_company_code}`" class="v-btn-solid">进入 {{ result.winner_company_name }} 工作台深潜</RouterLink>
              <RouterLink :to="`/competition/${result.winner_company_code}`" class="v-btn-outline">导出目标标的材料</RouterLink>
            </div>
          </div>
        </section>

      </article>
      
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';
import { api } from '../api/client';
import type { CompanyCompareResponse, CompanyComparisonRow } from '../api/types';
import { useDashboardStore } from '../stores/dashboard';

const route = useRoute();
const router = useRouter();
const store = useDashboardStore();

const selectedCodes = ref<string[]>([]);
const loadError = ref('');
const isLoading = ref(false);
const result = ref<CompanyCompareResponse | null>(null);

const targets = computed(() => store.targets);
const companies = computed<CompanyComparisonRow[]>(() => {
  return result.value ? result.value.comparison_rows.slice(0, 2) : [];
});

const evidenceCompanies = computed(() => {
  return result.value?.evidence?.companies?.slice(0, 2) || [];
});
const fromOverview = computed(() => route.query.entry === 'overview');

const exchangeLabels: Record<string, string> = { SSE: '上交所', SZSE: '深交所', BSE: '北交所' };

function formatExchange(val?: string | null) {
  return exchangeLabels[String(val || '').toUpperCase()] || String(val || '未知');
}

function formatNumber(val: number | null | undefined, fixed = 2) {
  if (val == null || !Number.isFinite(val)) return '-';
  return Number(val).toFixed(fixed);
}

function formatPercent(val: number | null | undefined) {
  if (val == null || !Number.isFinite(val)) return '-';
  return `${(Number(val)).toFixed(1)}%`;
}

function formatDate(val?: string | null) {
  if (!val) return '';
  return String(val).replace('T', ' ').slice(0, 10);
}

function scrollToSection(sectionId: string) {
  if (typeof document === 'undefined') return;
  document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function toggleCompany(code: string) {
  const index = selectedCodes.value.indexOf(code);
  if (index >= 0) {
    selectedCodes.value.splice(index, 1);
  } else {
    // Keep max 2
    if (selectedCodes.value.length >= 2) {
      selectedCodes.value.shift();
    }
    selectedCodes.value.push(code);
  }
}

function resetSelection() {
  const ranked = store.payload?.ranking || [];
  if (ranked.length >= 2) {
    selectedCodes.value = [String(ranked[0].company_code), String(ranked[1].company_code)];
  } else if (targets.value.length >= 2) {
    selectedCodes.value = [targets.value[0].company_code, targets.value[1].company_code];
  } else {
    selectedCodes.value = [];
  }
}

function parseUrlCodes() {
  const q = route.query.companies;
  if (typeof q === 'string' && q) {
    const arr = q.split(',').slice(0, 2).filter(Boolean);
    if (arr.length > 0) {
      selectedCodes.value = arr;
    }
  }
}

async function loadComparison() {
  if (selectedCodes.value.length < 2) return;
  isLoading.value = true;
  loadError.value = '';
  try {
    const codesStr = selectedCodes.value.join(',');
    result.value = await api.getCompanyCompare(selectedCodes.value);
    const nextQuery: Record<string, string> = { companies: codesStr };
    if (typeof route.query.entry === 'string') nextQuery.entry = route.query.entry;
    if (typeof route.query.focus === 'string') nextQuery.focus = route.query.focus;
    if (typeof route.query.company === 'string') nextQuery.company = route.query.company;
    void router.replace({ query: nextQuery });
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '企业对比暂时未能完成，请稍后重试';
    result.value = null;
  } finally {
    isLoading.value = false;
  }
}

onMounted(async () => {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  parseUrlCodes();
  if (selectedCodes.value.length === 0) {
    resetSelection();
  }
  if (selectedCodes.value.length >= 2) {
    void loadComparison();
  }
});

watch(() => route.query.companies, () => {
  parseUrlCodes();
});
</script>

<style scoped>
.v-document-page {
  background: var(--bg-base);
  min-height: 100vh;
  padding: 40px 20px 100px;
  color: var(--text-primary);
  font-family: 'DM Sans', -apple-system, sans-serif;
}

.v-doc-container {
  max-width: 900px;
  margin: 0 auto;
}

.v-compare-container {
  max-width: 1000px;
}

.v-doc-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 60px;
}

.v-back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.2s;
}

.v-back-link:hover {
  color: var(--text-primary);
}

.v-arrow {
  font-family: 'Syne', sans-serif;
  font-size: 16px;
}

.v-doc-header {
  border-bottom: 2px solid var(--text-primary);
  padding-bottom: 30px;
  margin-bottom: 40px;
}

.v-entry-note {
  display: grid;
  gap: 6px;
  margin: -8px 0 28px;
  padding: 16px 18px;
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  background: var(--bg-surface-soft);
}

.v-entry-note-label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-entry-note p {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.v-doc-title {
  font-family: 'Syne', sans-serif;
  font-size: 42px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 0 0 12px;
  color: var(--text-primary);
}

.v-doc-subtitle {
  font-size: 18px;
  color: var(--text-secondary);
  margin: 0;
}

.v-section-title {
  font-family: 'Syne', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-tertiary);
  margin: 0 0 24px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.v-doc-section {
  margin-bottom: 60px;
}

.v-config-stage {
  margin-bottom: 60px;
}

/* Selector Grid */
.v-target-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.v-target-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.v-target-btn:hover {
  border-color: var(--border-strong);
}

.v-target-btn.is-selected {
  border-color: var(--text-primary);
  background: var(--bg-surface-highlight);
  box-shadow: 0 0 0 1px var(--text-primary);
}

.v-exchange-tag {
  font-size: 12px;
  color: var(--text-tertiary);
}

.v-action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.v-status-note {
  margin: 16px 0 0;
  font-size: 13px;
  color: var(--status-error);
}

/* Actions */
.v-btn-solid {
  background: var(--text-primary);
  color: var(--bg-base);
  border: 1px solid transparent;
  padding: 10px 18px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  transition: background 0.2s;
}

.v-btn-solid:hover:not(:disabled) {
  background: #333;
}

.v-btn-solid:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.v-btn-outline {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-strong);
  padding: 10px 18px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  transition: background 0.2s;
}

.v-btn-outline:hover {
  background: var(--bg-surface-highlight);
}

/* Loader */
.v-loading-block {
  padding: 60px 0;
  text-align: center;
}

.v-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-subtle);
  border-top-color: var(--text-primary);
  border-radius: 50%;
  margin: 0 auto 20px;
  animation: v-spin 1s linear infinite;
}

@keyframes v-spin {
  to { transform: rotate(360deg); }
}

.v-error-block {
  padding: 40px;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  color: var(--status-error);
}

/* Verdict */
.v-verdict-banner {
  background: var(--bg-surface-highlight);
  border: 1px solid var(--border-subtle);
  padding: 30px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.v-verdict-label {
  display: inline-block;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-tertiary);
  margin-bottom: 8px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.v-verdict-winner {
  font-family: 'Syne', sans-serif;
  font-size: 32px;
  font-weight: 800;
  color: var(--brand-primary);
  margin: 0 0 16px;
}

.v-verdict-summary {
  font-size: 18px;
  line-height: 1.6;
  color: var(--text-primary);
  margin: 0;
}

.v-judgement-list {
  padding-left: 20px;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.7;
}

.v-judgement-list li {
  margin-bottom: 12px;
}

.v-company-brief-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.v-company-brief-card {
  display: grid;
  gap: 16px;
  padding: 22px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(246,248,251,0.98) 100%);
  box-shadow: var(--shadow-sm);
}

.v-company-brief-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.v-company-brief-head strong {
  display: block;
  font-size: 22px;
  line-height: 1.15;
  color: var(--text-primary);
}

.v-company-brief-head p {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
}

.v-company-brief-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.v-company-metric {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 8px;
  background: rgba(255,255,255,0.82);
  border: 1px solid var(--border-subtle);
}

.v-company-metric span {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-company-metric strong {
  font-size: 16px;
  line-height: 1.35;
  color: var(--text-primary);
}

.v-company-brief-copy {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.v-company-brief-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.v-nav-actions {
  display: grid;
  justify-items: end;
  gap: 10px;
}

.v-nav-actions-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-nav-action-cluster {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 12px;
}

.bottom-actions {
  justify-items: start;
}

.bottom-actions .v-nav-action-cluster {
  justify-content: flex-start;
}

/* Matrix */
.v-matrix {
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  background: var(--bg-surface);
  overflow: hidden;
}

.v-matrix-header {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1.5fr;
  background: var(--bg-surface-highlight);
  border-bottom: 2px solid var(--border-strong);
}

.v-matrix-col-title {
  padding: 16px 20px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-tertiary);
}

.v-matrix-col-target {
  padding: 16px 20px;
  font-family: 'Syne', sans-serif;
  font-size: 18px;
  color: var(--text-primary);
  border-left: 1px solid var(--border-subtle);
}

.v-matrix-row {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1.5fr;
  border-bottom: 1px solid var(--border-subtle);
  transition: background 0.2s;
}

.v-matrix-row:hover {
  background: rgba(0, 0, 0, 0.02);
}

.v-matrix-row:last-child {
  border-bottom: none;
}

.v-matrix-label {
  padding: 16px 20px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

.v-matrix-val {
  padding: 16px 20px;
  font-size: 16px;
  font-family: var(--font-mono);
  color: var(--text-primary);
  border-left: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
}

.v-winning-val {
  color: var(--brand-primary);
  font-weight: 700;
}

.v-risk-val {
  color: var(--status-error);
  font-weight: 700;
}

/* Dimensions grids */
.v-dimension-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.v-dimension-card {
  border: 1px solid var(--border-subtle);
  padding: 24px;
  border-radius: 8px;
  background: var(--bg-surface);
}

.v-dimension-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 16px;
  color: var(--text-primary);
}

.v-dimension-conclusion {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0 0 20px;
}

.v-badge {
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 700;
  border-radius: 4px;
  display: inline-block;
}

.v-badge-winner {
  background: var(--bg-surface-highlight);
  color: var(--brand-primary);
  border: 1px solid var(--border-strong);
}

@media (max-width: 768px) {
  .v-doc-nav,
  .v-target-grid,
  .v-company-brief-grid,
  .v-dimension-grid {
    grid-template-columns: 1fr;
  }
  .v-company-brief-metrics,
  .v-matrix-header,
  .v-matrix-row {
    grid-template-columns: 1fr;
  }
  .v-action-row,
  .v-nav-actions,
  .v-company-brief-actions,
  .v-nav-action-cluster {
    flex-direction: column;
    align-items: stretch;
    justify-content: flex-start;
  }
  .v-nav-actions {
    width: 100%;
    justify-items: stretch;
  }
  .v-matrix-col-target,
  .v-matrix-val {
    border-left: none;
    border-top: 1px solid var(--border-subtle);
  }
  .v-btn-solid,
  .v-btn-outline {
    width: 100%;
  }
}
</style>
