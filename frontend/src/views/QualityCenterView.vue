<template>
  <div class="page-stack v-document-page">
    <div class="v-doc-container">
      
      <!-- Top Nav -->
      <nav class="v-doc-nav">
        <RouterLink to="/" class="v-back-link">
          <span class="v-arrow">←</span> <span>返回中枢</span>
        </RouterLink>
        <div class="v-nav-actions">
          <button class="v-btn-outline" @click="loadSummary" :disabled="loading">实时刷新探针</button>
        </div>
      </nav>

      <!-- Strategy Header -->
      <header class="v-doc-header">
        <h1 class="v-doc-title">合规审计与可信底座</h1>
        <p class="v-doc-subtitle">全局数据湖仓实况、模型引擎状态监控及底层数据血缘追踪。</p>
      </header>

      <!-- Permissions Gate -->
      <div v-if="!authStore.canViewAudit" class="v-warning-banner" style="margin-bottom: 40px; margin-top: 0">
        <strong>权限受限</strong>
        <p>当前账号不具备系统级数据探针的查阅权限。如需获取审计报告，请联系数据质量团队。</p>
      </div>

      <template v-else>
        <!-- Loading State -->
        <div v-if="loading" class="v-loading-block">
          <div class="v-spinner"></div>
          <p>正在同步全网节点状态，拉取合规与质量探针，请稍候...</p>
        </div>

        <div v-else-if="summary" class="v-doc-body" style="margin-top: 20px;">
          
          <!-- Master Status -->
          <section class="v-doc-section">
            <h2 class="v-section-title">01 / 全局链路状态快照</h2>
            <div class="v-export-dashboard" style="margin-bottom: 24px;">
              <div class="v-export-stat">
                <span class="v-stat-label">权威财报覆盖度</span>
                <strong class="v-stat-val">{{ percent(summary.official_report_coverage_ratio) }}</strong>
              </div>
              <div class="v-export-stat">
                <span class="v-stat-label">拓展样本池装载</span>
                <strong class="v-stat-val">{{ summary.universe_report_downloaded_slots }} / {{ summary.universe_report_expected_slots }}</strong>
              </div>
              <div class="v-export-stat">
                <span class="v-stat-label">多模态解析率</span>
                <strong class="v-stat-val">{{ percent(summary.multimodal_extract_coverage_ratio) }}</strong>
              </div>
              <div class="v-export-stat">
                <span class="v-stat-label">阻断级拦截总量</span>
                <strong class="v-stat-val" :class="{ 'v-danger-text': summary.pending_review_count > 0 }">{{ summary.pending_review_count }} 项</strong>
              </div>
            </div>

            <!-- Anomaly Alerts -->
            <div class="v-anomaly-grid">
              <div class="v-anomaly-card">
                <div class="v-anomaly-head">
                  <strong>文件缺失拦截</strong>
                  <span class="v-danger-text">{{ summary.issue_breakdown.missing_reports }} 宗</span>
                </div>
                <p>底层文件物理断档，中断推演。</p>
              </div>
              <div class="v-anomaly-card">
                <div class="v-anomaly-head">
                  <strong>字段合规校验拦截</strong>
                  <span class="v-danger-text">{{ summary.issue_breakdown.field_gaps }} 批</span>
                </div>
                <p>结构解析版式变异引发降级。</p>
              </div>
              <div class="v-anomaly-card">
                <div class="v-anomaly-head">
                  <strong>多模态渲染停滞</strong>
                  <span class="v-warning-text">{{ summary.issue_breakdown.multimodal_missing }} 批</span>
                </div>
                <p>复杂矢量图大模型转译超时或异常。</p>
              </div>
              <div class="v-anomaly-card">
                <div class="v-anomaly-head">
                  <strong>认知熵过低拦截</strong>
                  <span class="v-warning-text">{{ summary.issue_breakdown.multimodal_low_coverage }} 笔</span>
                </div>
                <p>信息提取量低于可信研判阈值。</p>
              </div>
            </div>
          </section>

          <!-- Governance Matrix -->
          <section class="v-doc-section" v-if="governance">
            <h2 class="v-section-title">02 / 核准信源目录表</h2>
            
            <div class="v-data-table-wrapper">
              <table class="v-data-table">
                <thead>
                  <tr>
                    <th>资源名称与域</th>
                    <th>调用优先级</th>
                    <th>限定校验域</th>
                    <th>合规备注</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in governance.source_catalog" :key="item.source_name">
                    <td>
                      <strong class="v-text-primary">{{ item.source_name }}</strong>
                      <br/>
                      <span class="v-text-muted">{{ item.domain }}</span>
                    </td>
                    <td><span class="v-badge">{{ item.priority }}</span></td>
                    <td>{{ item.usage_scope }}</td>
                    <td class="v-text-muted">{{ item.compliance_note }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- System Stack & Engins -->
          <section class="v-doc-section" v-if="stack && stackPillars.length">
            <h2 class="v-section-title">03 / 分析引擎构件矩阵</h2>
            
            <div class="v-stack-grid">
              <div v-for="pillar in stackPillars" :key="pillar.pillar_id" class="v-stack-card">
                <div class="v-stack-head">
                  <div>
                    <span class="v-stat-label">{{ pillar.name }}</span>
                    <h3 class="v-stack-title">{{ pillar.stage_label }}</h3>
                  </div>
                  <div class="v-stack-score">
                    <strong>{{ formatReadiness(pillar.readiness_score) }}</strong>
                    <span>就绪指数</span>
                  </div>
                </div>
                <p class="v-stack-summary">{{ pillar.summary }}</p>
                <div class="v-stack-metrics">
                  <span v-for="metric in pillar.headline_metrics" :key="metric.label" class="v-badge" :class="metric.tone">
                    {{ metric.label }} {{ metric.value }}
                  </span>
                </div>
                <div class="v-stack-lines">
                  <div class="v-stack-line">
                    <strong class="v-text-primary">核心阵地</strong>
                    <span>{{ pillar.strengths[0] }}</span>
                  </div>
                  <div class="v-stack-line">
                    <strong class="v-danger-text">攻坚阻塞</strong>
                    <span>{{ pillar.gaps[0] }}</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- Data Preparation / Sourcing -->
          <section class="v-doc-section" v-if="preparation">
            <h2 class="v-section-title">04 / 大模型语料提纯 (SFT)</h2>
            <div class="v-export-split" style="gap:24px; row-gap:24px;">
              <div class="v-download-card">
                <div class="v-dl-icon">SFT</div>
                <div class="v-dl-info">
                  <strong>全域指令回流微调集</strong>
                  <p>样本总数: {{ preparation.multimodal_sft_sample_count }}</p>
                </div>
              </div>
              <div class="v-download-card">
                <div class="v-dl-icon">EXT</div>
                <div class="v-dl-info">
                  <strong>结构化知识抽取向量</strong>
                  <p>抽取总数: {{ preparation.multimodal_extract_count }}</p>
                </div>
              </div>
            </div>
          </section>

          <section class="v-doc-section" v-if="retrievalEvaluation">
            <h2 class="v-section-title">05 / 检索评测基线</h2>
            <p class="v-doc-subtitle v-section-intro">
              当前不是只看“能不能搜到”，而是持续量化命中率、排序质量和检索策略表现。
            </p>

            <div class="v-export-dashboard" style="margin-bottom: 24px;">
              <div class="v-export-stat">
                <span class="v-stat-label">评测样本数</span>
                <strong class="v-stat-val">{{ retrievalEvaluation.case_count }}</strong>
              </div>
              <div class="v-export-stat">
                <span class="v-stat-label">Hit@3</span>
                <strong class="v-stat-val">{{ percent(retrievalEvaluation.hit_at_3) }}</strong>
              </div>
              <div class="v-export-stat">
                <span class="v-stat-label">MRR</span>
                <strong class="v-stat-val">{{ scoreText(retrievalEvaluation.mrr) }}</strong>
              </div>
              <div class="v-export-stat">
                <span class="v-stat-label">nDCG@5</span>
                <strong class="v-stat-val">{{ scoreText(retrievalEvaluation.ndcg_at_5) }}</strong>
              </div>
            </div>

            <div class="v-retrieval-head">
              <div class="v-retrieval-mode">
                <strong>当前检索策略</strong>
                <p>{{ formatModeLabel(retrievalEvaluation.retrieval_mode || 'hybrid_tfidf_rerank') }}</p>
              </div>
              <div class="v-stack-metrics">
                <span v-for="label in retrievalEvaluation.strategy_labels" :key="label" class="v-badge neutral">
                  {{ label }}
                </span>
              </div>
            </div>

            <div
              v-if="retrievalEvaluation.strategy_benchmarks.length"
              class="v-retrieval-benchmark-grid"
            >
              <article
                v-for="item in retrievalEvaluation.strategy_benchmarks"
                :key="item.retrieval_mode"
                class="v-retrieval-benchmark-card"
                :class="{ best: retrievalEvaluation.best_mode === item.retrieval_mode }"
              >
                <div class="v-retrieval-benchmark-top">
                  <div>
                    <span class="v-stat-label">策略模式</span>
                    <h3 class="v-retrieval-benchmark-title">{{ formatModeLabel(item.retrieval_mode) }}</h3>
                  </div>
                  <div
                    v-if="retrievalEvaluation.best_mode === item.retrieval_mode"
                    class="v-retrieval-case-score success"
                  >
                    当前最佳
                  </div>
                </div>
                <div class="v-retrieval-benchmark-metrics">
                  <span>Hit@3 {{ percent(item.hit_at_3) }}</span>
                  <span>MRR {{ scoreText(item.mrr) }}</span>
                  <span>nDCG@5 {{ scoreText(item.ndcg_at_5) }}</span>
                </div>
                <p class="v-retrieval-case-line v-text-muted">
                  {{ item.strategy_labels.join('、') }}
                </p>
              </article>
            </div>

            <div
              v-if="retrievalEvaluation.comparison_notes.length"
              class="v-retrieval-notes"
            >
              <p
                v-for="note in retrievalEvaluation.comparison_notes"
                :key="note"
                class="v-retrieval-note"
              >
                {{ note }}
              </p>
            </div>

            <div class="v-retrieval-case-list">
              <article v-for="item in retrievalEvaluation.cases.slice(0, 4)" :key="item.case_id" class="v-retrieval-case">
                <div class="v-retrieval-case-top">
                  <div>
                    <span class="v-stat-label">{{ item.scope === 'company' ? '企业问答' : '行业问答' }}</span>
                    <h3 class="v-retrieval-case-title">{{ item.query }}</h3>
                  </div>
                  <div class="v-retrieval-case-score" :class="{ success: item.hit_at_3, warning: !item.hit_at_3 }">
                    {{ item.hit_at_3 ? 'Top3 命中' : 'Top3 未命中' }}
                  </div>
                </div>
                <div class="v-retrieval-case-metrics">
                  <span>MRR {{ scoreText(item.reciprocal_rank) }}</span>
                  <span>nDCG@5 {{ scoreText(item.ndcg_at_5) }}</span>
                </div>
                <p class="v-retrieval-case-line">
                  目标关键词：{{ item.relevant_keywords.join('、') }}
                </p>
                <p class="v-retrieval-case-line" v-if="item.matched_titles.length">
                  命中文档：{{ item.matched_titles.join('；') }}
                </p>
                <p class="v-retrieval-case-line v-text-muted" v-else>
                  当前 Top5 中尚未出现显式命中标题，需要继续优化召回与排序。
                </p>
              </article>
            </div>
          </section>

        </div>
      </template>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { api } from '../api/client';
import type {
  AIStackSummaryResponse,
  DataFoundationSummaryResponse,
  DataGovernanceSummaryResponse,
  DataPreparationSummaryResponse,
  QualitySummaryResponse,
  RetrievalEvaluationSummaryResponse,
  WarehouseSummaryResponse,
} from '../api/types';
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();
const loading = ref(false);

const summary = ref<QualitySummaryResponse | null>(null);
const foundation = ref<DataFoundationSummaryResponse | null>(null);
const governance = ref<DataGovernanceSummaryResponse | null>(null);
const preparation = ref<DataPreparationSummaryResponse | null>(null);
const retrievalEvaluation = ref<RetrievalEvaluationSummaryResponse | null>(null);
const stack = ref<AIStackSummaryResponse | null>(null);
const warehouse = ref<WarehouseSummaryResponse | null>(null);

const stackPillars = computed(() => stack.value?.pillars || []);

function percent(value: unknown) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '0%';
  return `${(value * 100).toFixed(1)}%`;
}

function formatReadiness(value: unknown) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'N/A';
  return (value * 100).toFixed(0);
}

function scoreText(value: unknown) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '0.000';
  return value.toFixed(3);
}

function formatModeLabel(value: string) {
  const mapping: Record<string, string> = {
    lexical_tfidf: 'Lexical TF-IDF',
    hybrid_tfidf_rerank: 'Hybrid TF-IDF + Rerank',
    hybrid_diversified: 'Hybrid Diversified',
  };
  return mapping[value] || value;
}

async function loadSummary() {
  if (!authStore.canViewAudit) return;
  loading.value = true;
  try {
    const [qSum, qFou, qGov, qPre, rEval, sSum, wSum] = await Promise.all([
      api.getQualitySummary(),
      api.getQualityFoundation(),
      api.getQualityGovernance(),
      api.getQualityPreparation(),
      api.getRetrievalEvaluation(),
      api.getAIStack(),
      api.getWarehouseSummary(),
    ]);
    summary.value = qSum;
    foundation.value = qFou;
    governance.value = qGov;
    preparation.value = qPre;
    retrievalEvaluation.value = rEval;
    stack.value = sSum;
    warehouse.value = wSum;
  } catch (error) {
    console.warn(error);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadSummary();
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
  justify-content: space-between;
  align-items: center;
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

.v-btn-outline {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-strong);
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.v-btn-outline:hover:not(:disabled) {
  background: var(--bg-surface-highlight);
}

.v-doc-header {
  border-bottom: 2px solid var(--text-primary);
  padding-bottom: 30px;
  margin-bottom: 40px;
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

.v-section-intro {
  margin-bottom: 20px;
  font-size: 15px;
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

/* Loading */
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

/* Dashboard Summary */
.v-export-dashboard {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 24px;
  background: var(--bg-surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
}

.v-export-stat {
  display: flex;
  flex-direction: column;
  gap: 8px;
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

.v-danger-text { color: var(--status-error) !important; }
.v-warning-text { color: #d97706 !important; }
.v-text-primary { color: var(--text-primary) !important; }
.v-text-muted { color: var(--text-tertiary) !important; }

/* Anomalies Grid */
.v-anomaly-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.v-anomaly-card {
  padding: 16px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-surface);
}

.v-anomaly-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.v-anomaly-head strong {
  font-size: 14px;
  color: var(--text-primary);
}

.v-anomaly-head span {
  font-size: 14px;
  font-weight: 700;
  font-family: var(--font-mono);
}

.v-anomaly-card p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

/* Base Tables */
.v-data-table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  background: var(--bg-surface);
}

.v-data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.v-data-table th, .v-data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 13px;
}

.v-data-table th {
  background: var(--bg-surface-highlight);
  color: var(--text-tertiary);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.v-data-table tr:last-child td {
  border-bottom: none;
}

.v-badge {
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 4px;
  background: var(--bg-surface-highlight);
  border: 1px solid var(--border-strong);
  color: var(--text-secondary);
  display: inline-block;
}

.v-badge.positive {
  color: var(--brand-primary);
  border-color: rgba(34,197,94,0.3);
  background: rgba(34,197,94,0.05);
}

/* Stack Matrix */
.v-stack-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.v-retrieval-head {
  display: grid;
  gap: 16px;
  margin-bottom: 20px;
}

.v-retrieval-mode {
  display: grid;
  gap: 6px;
  padding: 18px 20px;
  border: 1px solid var(--border-strong);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,248,250,0.98) 100%);
}

.v-retrieval-mode strong {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.v-retrieval-mode p {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.v-retrieval-case-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.v-retrieval-benchmark-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 20px;
}

.v-retrieval-benchmark-card {
  padding: 20px;
  border: 1px solid var(--border-strong);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,249,251,0.98) 100%);
  display: grid;
  gap: 12px;
}

.v-retrieval-benchmark-card.best {
  border-color: rgba(15, 111, 40, 0.35);
  box-shadow: 0 12px 30px rgba(15, 111, 40, 0.08);
}

.v-retrieval-benchmark-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.v-retrieval-benchmark-title {
  margin: 6px 0 0;
  font-size: 18px;
  line-height: 1.3;
  letter-spacing: -0.03em;
}

.v-retrieval-benchmark-metrics {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.v-retrieval-notes {
  display: grid;
  gap: 10px;
  margin-bottom: 20px;
}

.v-retrieval-note {
  margin: 0;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.v-retrieval-case {
  padding: 22px;
  border: 1px solid var(--border-strong);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,249,251,0.98) 100%);
  box-shadow: var(--shadow-sm);
  display: grid;
  gap: 12px;
}

.v-retrieval-case-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.v-retrieval-case-title {
  margin: 6px 0 0;
  font-size: 20px;
  line-height: 1.35;
  letter-spacing: -0.03em;
}

.v-retrieval-case-score {
  flex-shrink: 0;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  background: rgba(24, 24, 27, 0.06);
  color: var(--text-primary);
}

.v-retrieval-case-score.success {
  background: rgba(15, 111, 40, 0.1);
  color: #0f6f28;
}

.v-retrieval-case-score.warning {
  background: rgba(180, 83, 9, 0.12);
  color: #b45309;
}

.v-retrieval-case-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.v-retrieval-case-line {
  margin: 0;
  font-size: 14px;
  line-height: 1.65;
}

.v-stack-card {
  padding: 24px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-surface);
}

.v-stack-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.v-stack-title {
  font-size: 18px;
  font-weight: 700;
  margin: 8px 0 0;
  color: var(--text-primary);
}

.v-stack-score {
  text-align: right;
}

.v-stack-score strong {
  display: block;
  font-size: 24px;
  font-family: var(--font-mono);
  color: var(--brand-primary);
  line-height: 1;
}

.v-stack-score span {
  font-size: 10px;
  text-transform: uppercase;
  color: var(--text-tertiary);
  letter-spacing: 0.05em;
}

.v-stack-summary {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0 0 16px;
}

.v-stack-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.v-stack-lines {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-top: 1px solid var(--border-subtle);
  padding-top: 16px;
}

.v-stack-line {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.v-stack-line strong {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.v-stack-line span {
  font-size: 13px;
  color: var(--text-secondary);
}

/* SFT Cards */
.v-export-split {
  display: flex;
}

.v-download-card {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 24px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  box-shadow: var(--shadow-sm);
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
  font-size: 16px;
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--text-secondary);
}

.v-dl-info strong {
  display: block;
  font-size: 15px;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.v-dl-info p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

@media (max-width: 900px) {
  .v-export-dashboard {
    grid-template-columns: 1fr 1fr;
  }
  .v-anomaly-grid {
    grid-template-columns: 1fr;
  }
  .v-stack-grid {
    grid-template-columns: 1fr;
  }
  .v-retrieval-case-list {
    grid-template-columns: 1fr;
  }
  .v-retrieval-benchmark-grid {
    grid-template-columns: 1fr;
  }
  .v-export-split {
    flex-direction: column;
  }
}
</style>
