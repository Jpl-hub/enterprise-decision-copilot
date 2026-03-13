<template>
  <div class="page-stack v-document-page">
    <div class="v-doc-container">
      
      <!-- Top Nav / Back Action -->
      <nav class="v-doc-nav">
        <RouterLink to="/" class="v-back-link">
          <span class="v-arrow">←</span> <span>返回中枢</span>
        </RouterLink>
        <div class="v-nav-actions">
          <span class="v-nav-actions-label">页面动作</span>
          <div class="v-nav-action-cluster">
          <button v-if="allEvidence.length" class="v-btn-outline" @click="scrollToSection('evidence-section')">查看关键证据</button>
          <button class="v-btn-outline" @click="loadAll" :disabled="isLoading">刷新分析</button>
          <a
            v-if="primarySourceUrl"
            class="v-btn-outline"
            :href="primarySourceUrl"
            target="_blank"
            rel="noreferrer"
          >
            查看财报原件
          </a>
          <RouterLink v-if="selectedCode" :to="`/competition/${selectedCode}`" class="v-btn-solid">导出报告</RouterLink>
          </div>
        </div>
      </nav>

      <!-- Loading State -->
      <div v-if="isLoading" class="v-loading-block">
        <div class="v-spinner"></div>
        <p>正在整理企业判断、证据与风险信号...</p>
      </div>

      <!-- Error State -->
      <div v-if="loadError" class="v-error-block">
        <p><strong>企业分析暂时未能完成</strong></p>
        <p>{{ loadError }}</p>
      </div>

      <!-- Document Body -->
      <article v-if="!isLoading && brief" class="v-doc-body">
        
        <!-- Header: Target Identity -->
        <header class="v-doc-header">
          <div class="v-doc-meta">
            <span class="v-badge">{{ currentCompanyName }}</span>
            <span class="v-badge" v-if="companyIndustry">{{ companyIndustry }}</span>
            <span class="v-badge" v-if="brief?.verdict">{{ brief.verdict }}</span>
            <span class="v-badge v-badge-risk" v-if="risk?.risk_level === '高'">高风险</span>
            <span class="v-badge v-badge-warning" v-if="isStaleData">需复核时效</span>
          </div>
          <h1 class="v-doc-title">企业深度诊断报告</h1>
          <p class="v-doc-subtitle">针对 {{ currentCompanyName }} 的经营、风险及财务分析与判断。</p>
        </header>

        <div v-if="fromOverview" class="v-entry-note">
          <span class="v-entry-note-label">来自分析中枢</span>
          <p>已承接 {{ entryCompanyName || currentCompanyName }} 的首页上下文，可直接查看判断、证据与原始财报。</p>
        </div>

        <!-- Freshness / Stale Warning -->
        <div v-if="isStaleData" class="v-warning-banner">
          <strong>数据断档警示</strong>
          <p>{{ staleReasonText }}</p>
        </div>

        <!-- Section 1: Executive Summary -->
        <section class="v-doc-section">
          <h2 class="v-section-title">01 / 核心判断</h2>
          <div class="v-executive-summary">
            <p>{{ brief.executive_summary || brief.summary || brief.verdict }}</p>
          </div>

          <div class="v-signal-grid" v-if="brief">
            <div class="v-signal-card">
              <span>当前判断</span>
              <strong>{{ brief.verdict || '待形成判断' }}</strong>
              <p>作为当前企业的一阶管理建议，用于承接后续对比与导出。</p>
            </div>
            <div class="v-signal-card" v-if="risk">
              <span>风险等级</span>
              <strong>{{ risk.risk_level }}风险</strong>
              <p>基于经营指标、机构观点与模型推演综合判断。</p>
            </div>
            <div class="v-signal-card">
              <span>证据锚点</span>
              <strong>{{ allEvidence.length }} 条</strong>
              <p>已汇总财报原件、图表页锚点和研报片段。</p>
            </div>
            <div class="v-signal-card">
              <span>最新披露</span>
              <strong>{{ latestDisclosureLabel }}</strong>
              <p>{{ latestDisclosureDate || '披露日期同步中' }}</p>
            </div>
          </div>
          
          <div class="v-judgement-grid">
            <div class="v-judgement-col">
              <h3>关键论点</h3>
              <ul class="v-bullet-list">
                <li v-for="j in brief.key_judgements" :key="j">{{ j }}</li>
              </ul>
            </div>
            <div class="v-judgement-col">
              <h3>策略与动作建议</h3>
              <ul class="v-bullet-list">
                <li v-for="a in brief.action_recommendations" :key="a">{{ a }}</li>
              </ul>
            </div>
          </div>

          <div v-if="brief.evidence_highlights?.length" class="v-evidence-highlight-grid">
            <article v-for="item in brief.evidence_highlights" :key="item" class="v-evidence-highlight-card">
              <span>证据摘记</span>
              <p>{{ item }}</p>
            </article>
          </div>
        </section>

        <!-- Section 2: Evidence Trail -->
        <section id="evidence-section" class="v-doc-section v-evidence-section" v-if="allEvidence.length">
          <div class="v-section-heading-row">
            <h2 class="v-section-title">02 / 关键证据锚点</h2>
            <span class="v-section-count">{{ allEvidence.length }} 条直接证据</span>
          </div>
          <p class="v-section-desc">优先展示可直接回链的财报原件、图表页锚点与研报片段，避免判断与证据脱节。</p>
          
          <div class="v-evidence-grid">
            <div v-for="(ev, idx) in allEvidence" :key="`${ev.evidence_type}-${ev.source_url || ev.image_url || ev.page_label || idx}`" class="v-evidence-card">
              <div class="v-evidence-meta">
                <span class="v-ev-type">{{ formatEvidenceType(ev.evidence_type) }}</span>
                <span class="v-ev-source" v-if="ev.institution">{{ ev.institution }}</span>
                <span class="v-ev-date" v-if="ev.report_date">{{ formatDate(ev.report_date) }}</span>
              </div>
              
              <div v-if="ev.evidence_type === 'image' && ev.image_url" class="v-ev-image-box">
                <img :src="ev.image_url" :alt="ev.page_label || '证据截图'" loading="lazy" />
              </div>
              
              <div class="v-ev-content">
                <p v-if="ev.title" class="v-ev-title">{{ ev.title }}</p>
                <p v-if="ev.summary" class="v-ev-summary">{{ ev.summary }}</p>
                <p v-if="ev.page_label" class="v-ev-page-label">引用位置: {{ ev.page_label }}</p>
                <a class="v-ev-link" v-if="ev.source_url" :href="ev.source_url" target="_blank" rel="noreferrer">
                  查看原始文档 ↗
                </a>
              </div>
            </div>
          </div>
        </section>

        <!-- Section 3: Financial Baseline & Risk -->
        <section class="v-doc-section" v-if="report || risk">
          <h2 class="v-section-title">03 / 经营与风险拆解</h2>

          <div v-if="risk" class="v-text-block">
            <h3>风险穿透 (系统预估: {{ risk.risk_level }}风险)</h3>
            <p>{{ risk.summary }}</p>
            <ul class="v-bullet-list" v-if="risk.drivers && risk.drivers.length">
              <li v-for="d in risk.drivers" :key="d">{{ d }}</li>
            </ul>
            <div v-if="risk.monitoring_items?.length" class="v-monitoring-box">
              <strong>持续监测事项：</strong>
              <span>{{ risk.monitoring_items.join('；') }}</span>
            </div>
          </div>

          <div v-if="report" class="v-analysis-section-grid">
            <div v-for="sec in report.sections" :key="sec.title" class="v-text-block">
              <div class="v-report-card-head">
                <span>分析模块</span>
                <h3>{{ sec.title }}</h3>
              </div>
              <p>{{ sec.content }}</p>
            </div>
          </div>
        </section>

      </article>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import { api } from '../api/client';
import type {
  CompanyReportResponse,
  DecisionBriefResponse,
  RiskForecastResponse,
  UnifiedEvidence
} from '../api/types';
import { useAgentThreadStore } from '../stores/agentThread';
import { useDashboardStore } from '../stores/dashboard';

const props = defineProps<{ companyCode?: string }>();
const route = useRoute();
const store = useDashboardStore();
const agentStore = useAgentThreadStore();

const selectedCode = ref(props.companyCode || String(route.params.companyCode || ''));
const loadError = ref('');

const report = ref<CompanyReportResponse | null>(null);
const brief = ref<DecisionBriefResponse | null>(null);
const risk = ref<RiskForecastResponse | null>(null);

const isLoading = ref(false);

const currentCompanyName = computed(() => {
  return store.targets.find(t => String(t.company_code) === selectedCode.value)?.company_name || 
         brief.value?.company_name || 
         report.value?.company_name || 
         '当前企业';
});

const fromOverview = computed(() => route.query.entry === 'overview');
const entryCompanyName = computed(() => {
  const value = route.query.company;
  return typeof value === 'string' ? value : '';
});

const companyIndustry = computed(() => {
  return store.targets.find(t => String(t.company_code) === selectedCode.value)?.industry || '';
});

const primarySourceUrl = computed(() => {
  return (
    String(report.value?.evidence?.financial_source_url || brief.value?.evidence?.financial_source_url || risk.value?.evidence?.financial_source_url || '').trim() ||
    undefined
  );
});

// Stale & Freshness Logic
// Fallback to checking missing_expected_full_year_report or missing_annual_report if backend sends it in the response context.
// Assuming we extract it from `report.evidence.missing_expected_full_year_report` as agreed in the API spec wrapper.
const isStaleData = computed(() => {
  return Boolean(
    report.value?.evidence?.is_stale_data || 
    risk.value?.evidence?.is_stale_data || 
    brief.value?.evidence?.is_stale_data ||
    report.value?.evidence?.missing_expected_full_year_report
  );
});

const staleReasonText = computed(() => {
  const reason = report.value?.evidence?.stale_reason || '当前企业最近一期完整财报可能存在缺失或延迟披露，模型推演可能存在时效性折损。';
  return String(reason);
});

const latestDisclosureLabel = computed(() => {
  return String(
    report.value?.evidence?.latest_periodic_label ||
    brief.value?.evidence?.latest_periodic_label ||
    risk.value?.evidence?.latest_periodic_label ||
    '年报口径'
  );
});

const latestDisclosureDate = computed(() => {
  const value =
    report.value?.evidence?.latest_official_disclosure ||
    brief.value?.evidence?.latest_official_disclosure ||
    risk.value?.evidence?.latest_official_disclosure ||
    report.value?.evidence?.annual_report_published_at;
  return value ? formatDate(String(value)) : '';
});

// Unify all evidence from the three APIs
const allEvidence = computed<UnifiedEvidence[]>(() => {
  const evs: UnifiedEvidence[] = [];
  
  if (brief.value?.evidence?.evidences && Array.isArray(brief.value.evidence.evidences)) {
    evs.push(...(brief.value.evidence.evidences as UnifiedEvidence[]));
  }
  if (report.value?.evidence?.evidences && Array.isArray(report.value.evidence.evidences)) {
    evs.push(...(report.value.evidence.evidences as UnifiedEvidence[]));
  }
  if (risk.value?.evidence?.evidences && Array.isArray(risk.value.evidence.evidences)) {
    evs.push(...(risk.value.evidence.evidences as UnifiedEvidence[]));
  }
  
  // Dedup by source_url or image_url
  const seen = new Set<string>();
  return evs.filter((item) => {
    const key = String(item.source_url || item.image_url || item.page_label || item.title || `${item.evidence_type}-fallback`);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
});

function formatEvidenceType(type: string) {
  switch (type) {
    case 'image': return '多模态图表';
    case 'pdf_anchor': return '原件定位';
    case 'link': return '外部链接';
    case 'text': return '研报片段';
    default: return '事实证据';
  }
}

function formatDate(val?: string | null) {
  if (!val) return '';
  return String(val).replace('T', ' ').slice(0, 10);
}

function scrollToSection(sectionId: string) {
  if (typeof document === 'undefined') return;
  document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function loadAll() {
  if (!selectedCode.value) return;
  isLoading.value = true;
  loadError.value = '';
  try {
    const [reportResult, briefResult, riskResult] = await Promise.all([
      api.getCompanyReport(selectedCode.value),
      api.getDecisionBrief(selectedCode.value, `结合财报、研报和风险模型，给出${currentCompanyName.value}的经营判断和动作建议`),
      api.getRiskForecast(selectedCode.value),
    ]);
    report.value = reportResult;
    brief.value = briefResult;
    risk.value = riskResult;
    agentStore.setFocus(selectedCode.value, currentCompanyName.value);
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '企业分析暂时未能完成，请稍后重试';
  } finally {
    isLoading.value = false;
  }
}

watch(() => props.companyCode, (value) => {
  if (value) selectedCode.value = value;
});

watch(selectedCode, () => {
  if (selectedCode.value) {
    void loadAll();
  }
});

onMounted(() => {
  if (!store.payload && !store.loading) {
    void store.load();
  }
  if (!selectedCode.value && store.targets.length) {
    selectedCode.value = String(store.targets[0].company_code);
  }
  if (selectedCode.value) {
    void loadAll();
  }
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

.v-doc-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.v-btn-outline {
  background: transparent;
  border: 1px solid var(--border-strong);
  color: var(--text-primary);
  padding: 10px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 42px;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.v-btn-outline:hover:not(:disabled) {
  background: var(--bg-surface-highlight);
}

.v-btn-outline:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.v-btn-solid {
  background: var(--text-primary);
  color: var(--bg-base);
  border: 1px solid transparent;
  padding: 10px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
}

.v-btn-solid:hover {
  background: #333;
}

.v-loading-block, .v-error-block {
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

.v-error-block p {
  color: var(--status-error);
}

.v-doc-body {
  display: grid;
  gap: 80px;
  animation: v-fade-in 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes v-fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.v-doc-header {
  border-bottom: 2px solid var(--text-primary);
  padding-bottom: 30px;
}

.v-doc-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.v-badge {
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
}

.v-badge-risk {
  color: var(--status-error);
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.05);
}

.v-badge-warning {
  color: #b45309;
  border-color: rgba(217, 119, 6, 0.24);
  background: rgba(217, 119, 6, 0.08);
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

.v-warning-banner {
  background: rgba(245, 158, 11, 0.05);
  border: 1px solid rgba(245, 158, 11, 0.3);
  padding: 16px 20px;
  border-radius: 6px;
  margin-bottom: -40px;
}

.v-warning-banner strong {
  display: block;
  color: #d97706;
  font-size: 14px;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.v-warning-banner p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
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

.v-section-heading-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.v-section-count {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-executive-summary {
  font-size: 24px;
  font-weight: 500;
  line-height: 1.5;
  color: var(--text-primary);
  margin-bottom: 40px;
}

.v-signal-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 32px;
}

.v-signal-card {
  display: grid;
  gap: 8px;
  padding: 18px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(247,248,250,0.96) 100%);
  box-shadow: var(--shadow-sm);
}

.v-signal-card span {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-signal-card strong {
  font-size: 18px;
  line-height: 1.35;
  color: var(--text-primary);
}

.v-signal-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-secondary);
}

.v-judgement-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  padding-top: 30px;
  border-top: 1px solid var(--border-subtle);
}

.v-evidence-highlight-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 28px;
}

.v-evidence-highlight-card {
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  box-shadow: var(--shadow-sm);
}

.v-evidence-highlight-card span {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-evidence-highlight-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-primary);
}

.v-judgement-col h3, .v-text-block h3 {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 16px;
  color: var(--text-primary);
}

.v-bullet-list {
  margin: 0;
  padding: 0 0 0 18px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.v-bullet-list li {
  margin-bottom: 12px;
}

.v-text-block {
  margin-bottom: 0;
  padding: 20px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
  background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,248,250,0.98) 100%);
  box-shadow: var(--shadow-sm);
}

.v-text-block p {
  color: var(--text-secondary);
  line-height: 1.75;
  font-size: 15px;
  margin: 0;
}

.v-monitoring-box {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  padding: 16px;
  border-radius: 6px;
  font-size: 14px;
  margin-top: 20px;
}

.v-analysis-section-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.v-report-card-head {
  display: grid;
  gap: 6px;
  margin-bottom: 14px;
}

.v-report-card-head span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-monitoring-box strong {
  color: var(--status-error);
}

.v-section-desc {
  color: var(--text-secondary);
  margin: -16px 0 30px;
  font-size: 14px;
}

.v-evidence-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.v-evidence-card {
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-surface);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: var(--shadow-sm);
}

.v-evidence-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  font-size: 12px;
}

.v-ev-type {
  font-weight: 700;
  color: var(--text-primary);
  background: var(--bg-surface-highlight);
  padding: 2px 8px;
  border-radius: 4px;
}

.v-ev-source, .v-ev-date {
  color: var(--text-tertiary);
}

.v-ev-image-box {
  width: 100%;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  background: var(--bg-base);
}

.v-ev-image-box img {
  display: block;
  width: 100%;
  height: auto;
  object-fit: cover;
}

.v-ev-page-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 8px;
  font-family: var(--font-mono);
}

.v-ev-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.v-ev-summary {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0 0 10px;
}

.v-ev-link {
  display: inline-block;
  font-size: 13px;
  font-weight: 600;
  color: var(--brand-primary);
  text-decoration: none;
}

.v-ev-link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .v-doc-nav {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
  .v-nav-actions,
  .v-nav-action-cluster {
    width: 100%;
    justify-items: stretch;
    justify-content: flex-start;
  }
  .v-judgement-grid {
    grid-template-columns: 1fr;
    gap: 30px;
  }
  .v-signal-grid,
  .v-evidence-highlight-grid,
  .v-analysis-section-grid {
    grid-template-columns: 1fr;
  }
  .v-btn-outline,
  .v-btn-solid {
    width: 100%;
  }
  .v-executive-summary {
    font-size: 20px;
  }
  .v-section-heading-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
