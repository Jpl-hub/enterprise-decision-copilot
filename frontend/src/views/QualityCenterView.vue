<template>
  <div class="page-stack quality-page refined-quality-page">
    <PagePanel title="数据底座" eyebrow="Data Control Tower">
      <template #actions>
        <div class="toolbar-cluster">
          <button class="button-ghost" @click="syncAutoReviews" :disabled="loading || autoSyncing || !authStore.canAutoSyncReviews">自动复核</button>
          <button class="button-primary" @click="loadSummary" :disabled="loading">刷新</button>
        </div>
      </template>

      <div v-if="syncMessage" class="info-banner">{{ syncMessage }}</div>
      <div v-if="loading" class="empty-state">正在加载数据底座状态...</div>
      <template v-else-if="summary">
        <section class="control-tower-hero">
          <div class="tower-main-card">
            <div>
              <p class="section-tag">系统状态</p>
              <h3>{{ readinessHeadline }}</h3>
              <p>{{ readinessText }}</p>
            </div>
            <div class="tower-pill-row">
              <span class="tower-pill">财报 {{ percent(summary.official_report_coverage_ratio) }}</span>
              <span class="tower-pill">图表 {{ percent(summary.multimodal_extract_coverage_ratio) }}</span>
              <span class="tower-pill">复核 {{ summary.pending_review_count }} 条</span>
            </div>
          </div>

          <div class="tower-side-grid">
            <div class="tower-stat-card">
              <span>财报覆盖</span>
              <strong>{{ percent(summary.official_report_coverage_ratio) }}</strong>
              <div class="signal-meter"><div class="signal-meter-fill" :style="{ width: `${summary.official_report_coverage_ratio * 100}%` }"></div></div>
            </div>
            <div class="tower-stat-card">
              <span>图表抽取</span>
              <strong>{{ percent(summary.multimodal_extract_coverage_ratio) }}</strong>
              <div class="signal-meter"><div class="signal-meter-fill accent" :style="{ width: `${summary.multimodal_extract_coverage_ratio * 100}%` }"></div></div>
            </div>
            <div class="tower-stat-card warning">
              <span>待复核</span>
              <strong>{{ summary.pending_review_count }}</strong>
              <div class="signal-meter"><div class="signal-meter-fill warning" :style="{ width: pendingWidth }"></div></div>
            </div>
          </div>
        </section>

        <section class="data-flow-board">
          <div class="flow-card">
            <span>官方财报</span>
            <strong>{{ summary.official_report_downloaded_slots }}/{{ summary.official_report_expected_slots }}</strong>
            <p>三所正式披露年报已进入主分析链路。</p>
          </div>
          <div class="flow-arrow">→</div>
          <div class="flow-card">
            <span>多模态补全</span>
            <strong>{{ summary.multimodal_extract_report_count }}/{{ summary.multimodal_expected_report_count }}</strong>
            <p>图表、表格和跨页版式补成结构化字段。</p>
          </div>
          <div class="flow-arrow">→</div>
          <div class="flow-card">
            <span>质量复核</span>
            <strong>{{ summary.recent_reviews.length }}</strong>
            <p>异常自动入队，支持人工补充与复核闭环。</p>
          </div>
          <div class="flow-arrow">→</div>
          <div class="flow-card accent-card">
            <span>Agent 证据链</span>
            <strong>{{ summary.multimodal_backends.join(' / ') || '规则链路' }}</strong>
            <p>最终进入企业分析、对比和导出材料。</p>
          </div>
        </section>

        <div class="panel-split two-cols">
          <div class="sub-panel compact-data-panel">
            <div class="sub-panel-header">
              <h3>交易所接入</h3>
              <span class="badge-subtle">三所运行态</span>
            </div>
            <div class="stack-list">
              <div v-for="item in summary.exchange_status" :key="item.exchange" class="exchange-board-card">
                <div class="trace-title-row">
                  <strong>{{ item.exchange }}</strong>
                  <span>{{ item.downloaded_rows }}/{{ item.rows }}</span>
                </div>
                <div class="signal-meter top-gap"><div class="signal-meter-fill dark" :style="{ width: exchangeWidth(item) }"></div></div>
                <div class="exchange-board-meta">
                  <span>Manifest {{ item.manifest_exists ? '已就绪' : '缺失' }}</span>
                  <span>文件缺失 {{ item.file_missing_rows }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="sub-panel compact-data-panel">
            <div class="sub-panel-header">
              <h3>异常热区</h3>
              <span class="badge-subtle">优先处理</span>
            </div>
            <div class="stack-list">
              <div v-for="item in summary.top_anomalies.slice(0, 5)" :key="`${item.company_code}-${item.report_year}`" class="anomaly-heat-card">
                <div class="trace-title-row">
                  <strong>{{ item.company_name }}</strong>
                  <span>异常分 {{ item.anomaly_score }}</span>
                </div>
                <div class="signal-meter top-gap"><div class="signal-meter-fill warning" :style="{ width: `${Math.min(100, item.anomaly_score)}%` }"></div></div>
                <p>覆盖率 {{ percent(item.field_coverage_ratio) }} · {{ item.critical_fields_missing.join('、') || '字段齐备' }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-split two-cols">
          <div class="sub-panel compact-data-panel">
            <div class="sub-panel-header">
              <h3>图表抽取进展</h3>
              <span class="badge-subtle">多模态</span>
            </div>
            <div class="stack-list">
              <div v-for="item in summary.multimodal_recent_extracts.slice(0, 4)" :key="`${item.company_code}-${item.report_year}`" class="multimodal-board-card">
                <div class="trace-title-row">
                  <strong>{{ item.company_name || item.company_code }}</strong>
                  <span>{{ item.backend }}</span>
                </div>
                <div class="mini-bar-item top-gap">
                  <div class="mini-bar-head">
                    <span>字段补全</span>
                    <strong>{{ item.filled_field_count }}</strong>
                  </div>
                  <div class="mini-bar-track"><div class="mini-bar-fill" :style="{ width: multimodalFieldWidth(item.filled_field_count) }"></div></div>
                </div>
                <p>页面 {{ item.page_images.length }} 张 · {{ item.notes.join('；') || '已进入证据链' }}</p>
              </div>
            </div>
          </div>

          <div class="sub-panel compact-data-panel">
            <div class="sub-panel-header">
              <h3>人工复核</h3>
              <span class="badge-subtle">治理闭环</span>
            </div>
            <div class="stack-list">
              <div v-for="item in summary.recent_reviews.slice(0, 4)" :key="`${item.company_code}-${item.report_year}-${item.created_at}`" class="review-board-card">
                <div class="trace-title-row">
                  <strong>{{ item.company_code }} {{ item.report_year }}</strong>
                  <span>{{ item.status }}</span>
                </div>
                <p>{{ item.finding_level }} · {{ item.finding_type }}</p>
                <p>{{ item.note }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-split two-cols">
          <div class="sub-panel compact-data-panel">
            <h3>手动补充复核</h3>
            <p v-if="!authStore.canManageReviews" class="empty-state">当前账号仅查看数据底座状态。</p>
            <template v-else>
              <div class="form-grid">
                <input v-model="review.company_code" class="text-input" placeholder="公司代码" />
                <input v-model.number="review.report_year" class="text-input" type="number" placeholder="报告年度" />
                <input v-model="review.finding_level" class="text-input" placeholder="优先级" />
                <input v-model="review.finding_type" class="text-input" placeholder="问题类型" />
              </div>
              <textarea v-model="review.note" class="text-area" rows="5" placeholder="补充说明"></textarea>
              <div class="button-row left-align top-gap">
                <button class="button-primary" @click="submitReview">提交复核</button>
                <span v-if="submitMessage">{{ submitMessage }}</span>
              </div>
            </template>
          </div>

          <div class="sub-panel compact-data-panel">
            <h3>本轮重点</h3>
            <div class="stack-list">
              <div class="action-line-card"><p>先把异常分最高的企业复核完，再做正式导出。</p></div>
              <div class="action-line-card"><p>优先补齐图表抽取覆盖不足的报告，避免 Agent 引用残缺字段。</p></div>
              <div class="action-line-card"><p>财报覆盖达到稳定阈值后，再扩大企业池和行业池。</p></div>
            </div>
          </div>
        </div>
      </template>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { api } from '../api/client';
import type { ExchangeQualityStatus, QualitySummaryResponse } from '../api/types';
import PagePanel from '../components/PagePanel.vue';
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();
const loading = ref(false);
const autoSyncing = ref(false);
const summary = ref<QualitySummaryResponse | null>(null);
const submitMessage = ref('');
const syncMessage = ref('');
const review = ref({
  company_code: '300760',
  report_year: 2024,
  finding_level: 'high',
  finding_type: '字段异常',
  note: '',
});

const readinessHeadline = computed(() => {
  if (!summary.value) return '加载中';
  if (summary.value.pending_review_count >= 5) return '数据底座仍有高优先级异常';
  if (summary.value.official_report_coverage_ratio >= 0.8) return '数据底座已进入稳定运行';
  return '数据底座正在持续扩充';
});

const readinessText = computed(() => {
  if (!summary.value) return '正在汇总';
  return `当前财报覆盖 ${percent(summary.value.official_report_coverage_ratio)}，图表抽取覆盖 ${percent(summary.value.multimodal_extract_coverage_ratio)}，待复核 ${summary.value.pending_review_count} 条。`;
});

const pendingWidth = computed(() => `${Math.min(100, Math.max(12, (summary.value?.pending_review_count || 0) * 10))}%`);

function percent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function exchangeWidth(item: ExchangeQualityStatus) {
  if (!item.rows) return '8%';
  return `${Math.max(10, (item.downloaded_rows / item.rows) * 100)}%`;
}

function multimodalFieldWidth(count: number) {
  return `${Math.min(100, Math.max(12, count * 4))}%`;
}

async function loadSummary() {
  loading.value = true;
  try {
    summary.value = await api.getQualitySummary();
  } finally {
    loading.value = false;
  }
}

async function syncAutoReviews() {
  if (!authStore.canAutoSyncReviews) return;
  autoSyncing.value = true;
  try {
    const payload = await api.syncAutoReviews(12);
    summary.value = payload.summary;
    syncMessage.value = `新增 ${payload.created_count} 条复核任务，跳过 ${payload.skipped_count} 条重复问题。`;
  } finally {
    autoSyncing.value = false;
  }
}

async function submitReview() {
  if (!authStore.canManageReviews) return;
  const result = await api.submitReview(review.value);
  summary.value = result.summary;
  submitMessage.value = `${result.review.company_code} ${result.review.report_year} 已加入复核队列`;
  review.value.note = '';
}

onMounted(() => {
  void loadSummary();
});
</script>
