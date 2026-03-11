<template>
  <div class="page-stack quality-page">
    <PagePanel title="多源数据与可信度中心" eyebrow="Trust Layer" description="先判断数据够不够全、来源够不够真、问题是否已进入复核，再决定结论能不能直接用。">
      <template #actions>
        <div class="toolbar-cluster">
          <button class="button-ghost" @click="syncAutoReviews" :disabled="loading || autoSyncing">自动生成复核任务</button>
          <button class="button-primary" @click="loadSummary" :disabled="loading">刷新状态</button>
        </div>
      </template>
      <div v-if="syncMessage" class="info-banner">{{ syncMessage }}</div>
      <div v-if="loading" class="empty-state">正在加载可信度状态...</div>
      <div v-else-if="summary" class="page-stack">
        <div class="signal-grid">
          <div class="signal-card">
            <span class="signal-label">官方财报覆盖</span>
            <strong>{{ `${(summary.official_report_coverage_ratio * 100).toFixed(1)}%` }}</strong>
            <p>{{ summary.official_report_downloaded_slots }} / {{ summary.official_report_expected_slots }} 个年报槽位已入库</p>
          </div>
          <div class="signal-card">
            <span class="signal-label">图表与表格补全</span>
            <strong>{{ `${(summary.multimodal_extract_coverage_ratio * 100).toFixed(1)}%` }}</strong>
            <p>{{ summary.multimodal_extract_report_count }} / {{ summary.multimodal_expected_report_count }} 份报告已完成复杂版面抽取</p>
          </div>
          <div class="signal-card">
            <span class="signal-label">待复核问题</span>
            <strong>{{ summary.pending_review_count }}</strong>
            <p>当前异常企业 {{ summary.anomaly_company_count }} 家</p>
          </div>
          <div class="signal-card">
            <span class="signal-label">抽取后端</span>
            <strong>{{ summary.multimodal_backends.join(' / ') || '暂无' }}</strong>
            <p>平均补全字段 {{ summary.multimodal_avg_filled_field_count.toFixed(1) }} 项</p>
          </div>
        </div>

        <div class="panel-split two-cols">
          <div class="sub-panel">
            <h3>当前资料池由什么组成</h3>
            <div class="stack-list">
              <div class="info-card compact source-breakdown-card">
                <strong>交易所财报</strong>
                <p class="muted">三所正式披露文件是经营分析的主底座，当前已覆盖 {{ summary.official_report_downloaded_slots }} 个年报槽位。</p>
              </div>
              <div class="info-card compact source-breakdown-card">
                <strong>研究报告</strong>
                <p class="muted">个股和行业研报负责补充市场观点、竞争格局和景气判断，供 Agent 做证据交叉验证。</p>
              </div>
              <div class="info-card compact source-breakdown-card">
                <strong>宏观指标</strong>
                <p class="muted">宏观指标帮助判断外部环境与行业周期，不让结论只盯公司自己。</p>
              </div>
              <div class="info-card compact source-breakdown-card">
                <strong>图表与表格证据</strong>
                <p class="muted">复杂 PDF 里的表格、截图和跨页版式会被补成结构化证据，减少漏读和错读。</p>
              </div>
            </div>
          </div>
          <div class="sub-panel">
            <h3>三所财报接入情况</h3>
            <div class="stack-list">
              <div v-for="item in summary.exchange_status" :key="item.exchange" class="info-card compact exchange-status-card">
                <div class="trace-title-row">
                  <strong>{{ item.exchange }}</strong>
                  <span class="badge-subtle">{{ item.downloaded_rows }} / {{ item.rows }}</span>
                </div>
                <p class="muted">Manifest {{ item.manifest_exists ? '已就绪' : '缺失' }} · 文件缺失 {{ item.file_missing_rows }} 条</p>
                <p class="muted">覆盖企业：{{ item.companies.join('、') || '暂无' }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-split two-cols">
          <div class="sub-panel">
            <div class="sub-panel-header">
              <h3>高优先级异常</h3>
              <span class="badge-subtle">优先处理这些问题</span>
            </div>
            <div class="stack-list">
              <div v-for="item in summary.top_anomalies" :key="`${item.company_code}-${item.report_year}`" class="info-card compact anomaly-detail-card">
                <div class="trace-title-row">
                  <strong>{{ item.company_name }} {{ item.report_year }}</strong>
                  <span class="badge-subtle">异常分 {{ item.anomaly_score }}</span>
                </div>
                <p class="muted">覆盖率 {{ (item.field_coverage_ratio * 100).toFixed(1) }}% · {{ item.exchange || '交易所未标记' }}</p>
                <p class="muted">缺失字段：{{ item.critical_fields_missing.join('、') || '字段齐备' }}</p>
                <p class="muted">异常标记：{{ item.anomaly_flags.join('、') || '暂无' }}</p>
              </div>
            </div>
          </div>
          <div class="sub-panel">
            <div class="sub-panel-header">
              <h3>最近图表与表格补全</h3>
              <span class="badge-subtle">多模态补证据</span>
            </div>
            <div class="stack-list">
              <div v-for="item in summary.multimodal_recent_extracts" :key="`${item.company_code}-${item.report_year}`" class="info-card compact multimodal-card">
                <div class="trace-title-row">
                  <strong>{{ item.company_name || item.company_code }} {{ item.report_year }}</strong>
                  <span class="badge-subtle">{{ item.backend }}</span>
                </div>
                <p class="muted">识别字段 {{ item.filled_field_count }} 项 · 页面 {{ item.page_images.length }} 张</p>
                <p class="muted">说明：{{ item.notes.join('；') || '已进入正式证据链' }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-split two-cols">
          <div class="sub-panel">
            <div class="sub-panel-header">
              <h3>最近复核记录</h3>
              <span class="badge-subtle">治理闭环</span>
            </div>
            <div class="stack-list">
              <div v-for="item in summary.recent_reviews" :key="`${item.company_code}-${item.report_year}-${item.created_at}`" class="info-card compact review-record-card">
                <div class="trace-title-row">
                  <strong>{{ item.company_code }} {{ item.report_year }}</strong>
                  <span class="badge-subtle">{{ item.status }}</span>
                </div>
                <p class="muted">{{ item.finding_level }} · {{ item.finding_type }}</p>
                <p class="muted">{{ item.note }}</p>
              </div>
            </div>
          </div>
          <div class="sub-panel">
            <h3>手动补充复核</h3>
            <div class="form-grid">
              <input v-model="review.company_code" class="text-input" placeholder="公司代码" />
              <input v-model.number="review.report_year" class="text-input" type="number" placeholder="报告年度" />
              <input v-model="review.finding_level" class="text-input" placeholder="优先级" />
              <input v-model="review.finding_type" class="text-input" placeholder="问题类型" />
            </div>
            <textarea v-model="review.note" class="text-area" rows="5" placeholder="补充说明"></textarea>
            <div class="button-row left-align">
              <button class="button-primary" @click="submitReview">提交复核</button>
              <span class="muted" v-if="submitMessage">{{ submitMessage }}</span>
            </div>
          </div>
        </div>
      </div>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { api } from '../api/client';
import type { QualitySummaryResponse } from '../api/types';
import PagePanel from '../components/PagePanel.vue';

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

async function loadSummary() {
  loading.value = true;
  try {
    summary.value = await api.getQualitySummary();
  } finally {
    loading.value = false;
  }
}

async function syncAutoReviews() {
  autoSyncing.value = true;
  try {
    const payload = await api.syncAutoReviews(12);
    summary.value = payload.summary;
    syncMessage.value = `本次新增 ${payload.created_count} 条自动复核任务，跳过 ${payload.skipped_count} 条重复问题。`;
  } finally {
    autoSyncing.value = false;
  }
}

async function submitReview() {
  const result = await api.submitReview(review.value);
  summary.value = result.summary;
  submitMessage.value = `${result.review.company_code} ${result.review.report_year} 已加入复核队列`;
  review.value.note = '';
}

onMounted(() => {
  void loadSummary();
});
</script>
