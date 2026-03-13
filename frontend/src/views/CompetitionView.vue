<template>
  <div class="page-stack v-document-page">
    <div class="v-doc-container">
      
      <!-- Top Nav -->
      <nav class="v-doc-nav">
        <RouterLink to="/" class="v-back-link">
          <span class="v-arrow">←</span> <span>返回中枢</span>
        </RouterLink>
        <div v-if="selectedCode" class="v-nav-actions">
          <span class="v-nav-actions-label">页面动作</span>
          <div class="v-nav-action-cluster">
            <button v-if="result?.citations?.length" class="v-btn-outline" @click="scrollToSection('citation-section')">查看证据清单</button>
            <RouterLink :to="`/workbench/${selectedCode}`" class="v-btn-outline">返回企业分析</RouterLink>
          </div>
        </div>
      </nav>

      <!-- Strategy Header -->
      <header class="v-doc-header">
        <div class="v-header-kicker">正式材料 · 证据归档 · Markdown 成稿</div>
        <h1 class="v-doc-title">分析报告与材料导出</h1>
        <p class="v-doc-subtitle">把企业分析结论整理成可汇报、可追溯、可继续加工的正式材料。</p>
      </header>

      <div v-if="fromOverview" class="v-entry-note">
        <span class="v-entry-note-label">来自分析中枢</span>
        <p>已承接首页中的焦点企业与问题语境，当前材料可直接用于汇报、归档或继续加工。</p>
      </div>

      <!-- Permissions Gate -->
      <div v-if="!authStore.canExport" class="v-warning-banner" style="margin-bottom: 40px; margin-top: 0">
        <strong>权限受限</strong>
        <p>当前账号权限不足。如需导出正式报告材料，请联系系统管理员或高级分析员。</p>
      </div>
      
      <template v-else>
        
        <!-- Selection Stage -->
        <section class="v-doc-section">
          <h2 class="v-section-title">01 / 选择导出对象</h2>
          <p class="v-section-intro">先锁定企业，再整理一份可直接汇报、存档或二次加工的正式材料包。</p>
          <div class="v-export-controls">
            <label class="v-console-field">
              <select v-model="selectedCode" class="v-select-input">
                <option value="" disabled>— 请选择企业 —</option>
                <option v-for="item in targets" :key="item.company_code" :value="item.company_code">
                  {{ item.company_name }}
                </option>
              </select>
            </label>
            <button class="v-btn-solid" @click="loadPackage" :disabled="loading || !selectedCode">
              {{ loading ? '正在整理正式材料...' : '生成正式材料' }}
            </button>
          </div>
        </section>

        <!-- Loading State -->
        <div v-if="loading" class="v-loading-block">
          <div class="v-spinner"></div>
          <p>正在整理结论、证据与导出文件，请稍候...</p>
        </div>

        <!-- Result Stage -->
        <div v-else-if="result" class="v-doc-body" style="margin-top: 40px;">

          <section class="v-doc-section">
            <div class="v-material-hero">
              <div class="v-material-meta">
                <span class="v-badge">{{ result.company_name }}</span>
                <span class="v-badge subtle">{{ result.company_code }}</span>
                <span class="v-badge subtle">{{ result.report_year }} 年口径</span>
                <span v-if="result.brief_verdict" class="v-badge verdict">{{ result.brief_verdict }}</span>
                <span v-if="result.risk_level" class="v-badge risk">{{ result.risk_level }}风险</span>
              </div>
              <h2 class="v-material-title">正式材料已准备完成</h2>
              <p class="v-material-summary">{{ result.summary }}</p>
              <div class="v-material-question">
                <strong>本轮任务</strong>
                <p>{{ result.question }}</p>
              </div>
              <div v-if="result.evidence_digest" class="v-material-signals">
                <div class="v-signal-card">
                  <span>图表抽取</span>
                  <strong>{{ result.evidence_digest.multimodal_field_count || 0 }} 项字段</strong>
                </div>
                <div class="v-signal-card">
                  <span>语义证据</span>
                  <strong>{{ (result.evidence_digest.semantic_stock_count || 0) + (result.evidence_digest.semantic_industry_count || 0) }} 条</strong>
                </div>
                <div class="v-signal-card">
                  <span>待复核事项</span>
                  <strong>{{ result.evidence_digest.pending_review_count || 0 }} 项</strong>
                </div>
                <div class="v-signal-card">
                  <span>最新披露</span>
                  <strong>{{ result.evidence_digest.latest_periodic_label || '年报口径' }}</strong>
                </div>
              </div>
            </div>
          </section>
          
          <div class="v-export-dashboard">
            <div class="v-export-stat">
              <span class="v-stat-label">引用证据</span>
              <strong class="v-stat-val">{{ result.citation_count }} 条</strong>
            </div>
            <div class="v-export-stat">
              <span class="v-stat-label">导出口径</span>
              <strong class="v-stat-val">{{ result.report_year || '全年' }}</strong>
            </div>
            <div class="v-export-stat">
              <span class="v-stat-label">企业代码</span>
              <strong class="v-stat-val">{{ result.company_code }}</strong>
            </div>
            <div class="v-export-stat">
              <span class="v-stat-label">导出日期</span>
              <strong class="v-stat-val">{{ (result.exported_at || '').slice(0, 10) }}</strong>
            </div>
          </div>

          <section v-if="result.evidence_digest" class="v-doc-section">
            <h2 class="v-section-title">02 / 核心信号</h2>
            <div class="v-signal-grid">
              <div class="v-signal-detail">
                <span class="v-signal-detail-label">判断结论</span>
                <strong>{{ result.brief_verdict || '待形成判断' }}</strong>
                <p>风险等级 {{ result.risk_level || '同步中' }}，可直接承接后续汇报或横向比较。</p>
              </div>
              <div class="v-signal-detail">
                <span class="v-signal-detail-label">检索覆盖</span>
                <strong>{{ result.evidence_digest.semantic_stock_count || 0 }} 条个股 + {{ result.evidence_digest.semantic_industry_count || 0 }} 条行业</strong>
                <p v-if="result.evidence_digest.query_terms?.length">命中主题词：{{ result.evidence_digest.query_terms.join('、') }}</p>
                <p v-else>当前已按财报与研报主线完成整理。</p>
              </div>
              <div class="v-signal-detail">
                <span class="v-signal-detail-label">披露与治理</span>
                <strong>{{ result.evidence_digest.latest_official_disclosure || '同步中' }}</strong>
                <p>
                  {{ result.evidence_digest.company_anomaly_count || 0 }} 条异常，
                  {{ result.evidence_digest.company_review_queue_count || 0 }} 条企业复核队列。
                </p>
              </div>
            </div>
          </section>

          <section v-if="result.publication_gate || result.data_authenticity" class="v-doc-section">
            <h2 class="v-section-title">03 / 发布门禁</h2>
            <div class="v-gate-panel">
              <div class="v-gate-summary">
                <span class="v-signal-detail-label">门禁状态</span>
                <strong>{{ result.publication_gate?.gate_status || 'pending' }}</strong>
                <p>{{ String(result.publication_gate?.statement || result.data_authenticity?.statement || '系统正在生成真实性说明。') }}</p>
              </div>
              <div class="v-gate-meta">
                <div class="v-gate-chip" :class="`is-${result.publication_gate?.system_trust_status || 'unknown'}`">
                  系统信任：{{ result.publication_gate?.system_trust_status || 'unknown' }}
                </div>
                <div class="v-gate-chip" :class="`is-${result.publication_gate?.package_trust_status || 'unknown'}`">
                  材料信任：{{ result.publication_gate?.package_trust_status || 'unknown' }}
                </div>
                <div class="v-gate-chip" :class="{ 'is-approved': result.publication_gate?.enterprise_ready }">
                  正式输出：{{ result.publication_gate?.enterprise_ready ? '允许' : '需复核/阻断' }}
                </div>
              </div>
              <div v-if="Array.isArray(result.publication_gate?.blocking_reasons) && result.publication_gate?.blocking_reasons?.length" class="v-gate-list">
                <strong>阻断原因</strong>
                <p v-for="item in result.publication_gate.blocking_reasons" :key="String(item)">{{ item }}</p>
              </div>
              <div v-if="Array.isArray(result.publication_gate?.warnings) && result.publication_gate?.warnings?.length" class="v-gate-list">
                <strong>复核提示</strong>
                <p v-for="item in result.publication_gate.warnings" :key="String(item)">{{ item }}</p>
              </div>
            </div>
          </section>

          <section class="v-doc-section">
            <h2 class="v-section-title">04 / 导出文件</h2>
            <div class="v-download-grid">
              <div class="v-download-card">
                <div class="v-dl-icon">M⬇</div>
                <div class="v-dl-info">
                  <strong>Markdown 材料原件</strong>
                  <p>{{ result.markdown_path || '服务端尚未持久化' }}</p>
                </div>
              </div>
              <div class="v-download-card">
                <div class="v-dl-icon">Z⬇</div>
                <div class="v-dl-info">
                  <strong>证据归档文件</strong>
                  <p>{{ result.evidence_path || '服务端尚未持久化' }}</p>
                </div>
              </div>
            </div>
          </section>

          <section class="v-doc-section v-export-split">

            <div class="v-split-left">
              <h2 class="v-section-title">05 / 材料结构</h2>
              <div class="v-outline-list">
                <div v-for="(section, idx) in result.sections" :key="section.title" class="v-outline-item">
                  <div class="v-outline-id">{{ String(idx + 1).padStart(2, '0') }}</div>
                  <div class="v-outline-text">
                    <strong>{{ section.title }}</strong>
                    <p>{{ section.content }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="v-split-right">
              <h2 id="citation-section" class="v-section-title">06 / 证据清单</h2>
              <div class="v-citation-list">
                <div v-for="item in result.citations" :key="item.citation_id" class="v-citation-item">
                  <div class="v-cite-head">
                    <strong>[{{ item.citation_id }}]</strong>
                    <span class="v-badge">{{ item.source_type }}</span>
                  </div>
                  <p class="v-cite-title">{{ item.title }}</p>
                  <p class="v-cite-meta">{{ [item.report_date, item.institution].filter(Boolean).join(' · ') }}</p>
                  <p v-if="item.excerpt" class="v-cite-excerpt">{{ item.excerpt }}</p>
                  <a v-if="item.source_url" class="v-cite-link" :href="item.source_url" target="_blank" rel="noreferrer">
                    查看原始来源 ↗
                  </a>
                </div>
              </div>
            </div>

          </section>

          <section class="v-doc-section">
            <h2 class="v-section-title">07 / Markdown 成稿预览</h2>
            <div class="v-markdown-box">
              <pre>{{ result.markdown_content }}</pre>
            </div>
          </section>

        </div>

      </template>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { api } from '../api/client';
import type { CompetitionPackageResponse } from '../api/types';
import { useAuthStore } from '../stores/auth';
import { useDashboardStore } from '../stores/dashboard';

const props = defineProps<{ companyCode?: string }>();
const route = useRoute();
const authStore = useAuthStore();
const store = useDashboardStore();

const selectedCode = ref(props.companyCode || '');
const loading = ref(false);
const result = ref<CompetitionPackageResponse | null>(null);
const targets = computed(() => store.targets);
const fromOverview = computed(() => route.query.entry === 'overview');

async function loadTargets() {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  if (!selectedCode.value && store.targets.length) {
    selectedCode.value = props.companyCode || String(route.params.companyCode || store.targets[0].company_code);
  }
}

async function loadPackage() {
  if (!selectedCode.value || !authStore.canExport) return;
  loading.value = true;
  try {
    const companyName = targets.value.find((item) => item.company_code === selectedCode.value)?.company_name || '该企业';
    result.value = await api.getCompetitionPackage(selectedCode.value, `结合真实数据为${companyName}生成企业运营分析材料`, true);
  } finally {
    loading.value = false;
  }
}

function scrollToSection(sectionId: string) {
  if (typeof document === 'undefined') return;
  document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

watch(() => props.companyCode, (value) => {
  if (value) selectedCode.value = value;
});

onMounted(async () => {
  await loadTargets();
  if (selectedCode.value && authStore.canExport) {
    await loadPackage();
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

.v-header-kicker {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  margin-bottom: 14px;
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.84);
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
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

.v-section-intro {
  margin: -10px 0 20px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.v-material-hero {
  display: grid;
  gap: 18px;
  padding: 28px 30px;
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,248,250,0.98) 100%);
  box-shadow: var(--shadow-md);
}

.v-material-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.v-badge.subtle {
  background: #f6f8fb;
  color: var(--text-secondary);
}

.v-badge.verdict {
  background: rgba(15, 23, 42, 0.92);
  color: #fff;
  border-color: rgba(15, 23, 42, 0.92);
}

.v-badge.risk {
  background: rgba(217, 119, 6, 0.1);
  color: #b45309;
  border-color: rgba(217, 119, 6, 0.3);
}

.v-material-title {
  margin: 0;
  font-size: 34px;
  line-height: 1.05;
  letter-spacing: -0.04em;
  font-family: 'Syne', sans-serif;
}

.v-material-summary {
  margin: 0;
  font-size: 17px;
  line-height: 1.75;
  color: var(--text-secondary);
  max-width: 780px;
}

.v-material-question {
  display: grid;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--border-subtle);
}

.v-material-question strong {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
}

.v-material-question p {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-primary);
}

.v-material-signals {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.v-signal-card {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.78);
}

.v-signal-card span {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-signal-card strong {
  font-size: 16px;
  line-height: 1.35;
  color: var(--text-primary);
}

.v-warning-banner {
  background: rgba(245, 158, 11, 0.05);
  border: 1px solid rgba(245, 158, 11, 0.3);
  padding: 16px 20px;
  border-radius: 6px;
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

/* Controls */
.v-export-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.v-console-field {
  flex: 1;
  max-width: 400px;
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

.v-btn-solid {
  background: var(--text-primary);
  color: var(--bg-base);
  border: 1px solid transparent;
  padding: 10px 18px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
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

/* State & Spinners */
.v-loading-block {
  padding: 80px 0;
  text-align: center;
  color: var(--text-secondary);
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

/* Result Blocks */
.v-export-dashboard {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 40px;
  padding: 24px;
  background: var(--bg-surface-highlight);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
}

.v-export-stat {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.v-signal-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.v-signal-detail {
  display: grid;
  gap: 8px;
  padding: 20px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: var(--bg-surface);
  box-shadow: var(--shadow-sm);
}

.v-signal-detail-label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-signal-detail strong {
  font-size: 20px;
  line-height: 1.25;
  color: var(--text-primary);
}

.v-signal-detail p {
  margin: 0;
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-secondary);
}

.v-stat-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-tertiary);
  letter-spacing: 0.05em;
}

.v-stat-val {
  font-size: 18px;
  font-family: var(--font-mono);
  color: var(--text-primary);
}

.v-download-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.v-gate-panel {
  display: grid;
  gap: 16px;
  padding: 24px;
  border: 1px solid var(--border-strong);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,249,251,0.96) 100%);
}

.v-gate-summary {
  display: grid;
  gap: 8px;
}

.v-gate-summary strong {
  font-size: 22px;
  color: var(--text-primary);
  text-transform: uppercase;
}

.v-gate-summary p {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.v-gate-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.v-gate-chip {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.v-gate-chip.is-trusted,
.v-gate-chip.is-approved {
  background: rgba(21, 128, 61, 0.1);
  border-color: rgba(21, 128, 61, 0.24);
  color: #166534;
}

.v-gate-chip.is-watch,
.v-gate-chip.is-review_required {
  background: rgba(217, 119, 6, 0.12);
  border-color: rgba(217, 119, 6, 0.26);
  color: #b45309;
}

.v-gate-chip.is-blocked,
.v-gate-chip.is-limited,
.v-gate-chip.is-at_risk {
  background: rgba(185, 28, 28, 0.1);
  border-color: rgba(185, 28, 28, 0.24);
  color: #b91c1c;
}

.v-gate-list {
  display: grid;
  gap: 8px;
  padding-top: 4px;
}

.v-gate-list strong {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-gate-list p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.v-download-card {
  display: flex;
  gap: 16px;
  padding: 24px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s, box-shadow 0.2s;
}

.v-download-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--border-strong);
}

.v-dl-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  font-size: 20px;
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--text-secondary);
}

.v-dl-info strong {
  display: block;
  font-size: 16px;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.v-dl-info p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.v-export-split {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 40px;
}

/* Outline List */
.v-outline-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.v-outline-item {
  display: flex;
  gap: 16px;
}

.v-outline-id {
  font-family: 'Syne', sans-serif;
  font-size: 24px;
  font-weight: 800;
  color: var(--text-tertiary);
  opacity: 0.5;
  margin-top: -4px;
}

.v-outline-text strong {
  display: block;
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.v-outline-text p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

/* Citation List */
.v-citation-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.v-citation-item {
  padding: 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
}

.v-cite-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.v-cite-head strong {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-tertiary);
}

.v-badge {
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 4px;
  background: var(--bg-surface-highlight);
  border: 1px solid var(--border-strong);
  color: var(--text-secondary);
}

.v-cite-title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.v-cite-meta {
  margin: 0;
  font-size: 12px;
  color: var(--text-tertiary);
}

.v-cite-excerpt {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-secondary);
}

.v-cite-link {
  display: inline-block;
  margin-top: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  text-decoration: none;
}

.v-cite-link:hover {
  text-decoration: underline;
}

/* Markdown pre */
.v-markdown-box {
  background: var(--bg-surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 24px;
  overflow: auto;
  max-height: 600px;
}

.v-markdown-box pre {
  margin: 0;
  font-family: 'DM Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-all;
}

@media (max-width: 900px) {
  .v-doc-nav {
    flex-direction: column;
    align-items: flex-start;
  }
  .v-nav-actions,
  .v-nav-action-cluster {
    width: 100%;
    justify-items: stretch;
    justify-content: flex-start;
  }
  .v-export-dashboard {
    grid-template-columns: 1fr 1fr;
  }
  .v-material-signals,
  .v-signal-grid {
    grid-template-columns: 1fr 1fr;
  }
  .v-export-split {
    grid-template-columns: 1fr;
  }
  .v-download-grid {
    grid-template-columns: 1fr;
  }
  .v-material-title {
    font-size: 28px;
  }
}

@media (max-width: 640px) {
  .v-export-controls,
  .v-nav-action-cluster {
    flex-direction: column;
  }
  .v-btn-solid,
  .v-btn-outline {
    width: 100%;
  }
  .v-material-signals,
  .v-signal-grid,
  .v-export-dashboard {
    grid-template-columns: 1fr;
  }
}
</style>
