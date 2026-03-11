<template>
  <div class="page-stack">
    <PagePanel title="数据治理中心" eyebrow="Trust Layer" description="这里不是附属页，而是整个 Agent 系统的可信度底座：官方数据覆盖、多模态抽取、异常复核和人工治理都在这里收口。">
      <div class="button-row">
        <button class="button-primary" @click="loadSummary">刷新治理状态</button>
      </div>
      <div v-if="loading" class="empty-state">正在加载质量摘要...</div>
      <div v-else-if="summary" class="page-stack">
        <div class="signal-grid">
          <div class="signal-card">
            <span class="signal-label">官方财报覆盖</span>
            <strong>{{ `${(summary.official_report_coverage_ratio * 100).toFixed(1)}%` }}</strong>
            <p>{{ summary.official_report_downloaded_slots }} / {{ summary.official_report_expected_slots }} 槽位</p>
          </div>
          <div class="signal-card">
            <span class="signal-label">多模态抽取覆盖</span>
            <strong>{{ `${(summary.multimodal_extract_coverage_ratio * 100).toFixed(1)}%` }}</strong>
            <p>{{ summary.multimodal_extract_report_count }} / {{ summary.multimodal_expected_report_count }} 份报告</p>
          </div>
          <div class="signal-card">
            <span class="signal-label">待复核任务</span>
            <strong>{{ summary.pending_review_count }}</strong>
            <p>异常企业 {{ summary.anomaly_company_count }} 家</p>
          </div>
          <div class="signal-card">
            <span class="signal-label">抽取后端</span>
            <strong>{{ summary.multimodal_backends.join(' / ') || '暂无' }}</strong>
            <p>平均识别字段 {{ summary.multimodal_avg_filled_field_count.toFixed(1) }}</p>
          </div>
        </div>

        <div class="panel-split two-cols">
          <div class="sub-panel">
            <h3>高优先级异常</h3>
            <div class="stack-list">
              <div v-for="item in summary.top_anomalies" :key="`${item.company_code}-${item.report_year}`" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.company_name }} {{ item.report_year }}</strong>
                  <span class="badge-subtle">{{ item.exchange }}</span>
                </div>
                <p class="muted">覆盖率 {{ (item.field_coverage_ratio * 100).toFixed(1) }}% · {{ item.critical_fields_missing.join('、') || '字段齐备' }}</p>
              </div>
            </div>
          </div>
          <div class="sub-panel">
            <h3>最近多模态抽取</h3>
            <div class="stack-list">
              <div v-for="item in summary.multimodal_recent_extracts" :key="`${item.company_code}-${item.report_year}`" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.company_name || item.company_code }} {{ item.report_year }}</strong>
                  <span class="badge-subtle">{{ item.backend }}</span>
                </div>
                <p class="muted">识别字段 {{ item.filled_field_count }} 项 · 页面 {{ item.page_images.length }} 张</p>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-split two-cols">
          <div class="sub-panel">
            <h3>人工复核登记</h3>
            <div class="form-grid">
              <input v-model="review.company_code" class="text-input" placeholder="公司代码" />
              <input v-model.number="review.report_year" class="text-input" type="number" placeholder="报告年度" />
              <input v-model="review.finding_level" class="text-input" placeholder="优先级" />
              <input v-model="review.finding_type" class="text-input" placeholder="问题类型" />
            </div>
            <textarea v-model="review.note" class="text-area" rows="5" placeholder="补充说明"></textarea>
            <div class="button-row">
              <button class="button-primary" @click="submitReview">提交复核</button>
              <span class="muted" v-if="submitMessage">{{ submitMessage }}</span>
            </div>
          </div>
          <div class="sub-panel">
            <h3>治理原则</h3>
            <div class="stack-list">
              <div class="info-card compact">
                <strong>结论要可追溯</strong>
                <p class="muted">每条结论都能回到官方财报、研报或多模态抽取记录。</p>
              </div>
              <div class="info-card compact">
                <strong>异常要可处理</strong>
                <p class="muted">抽取失败、字段缺失、质量异常会进入治理队列，而不是被静默忽略。</p>
              </div>
              <div class="info-card compact">
                <strong>系统口径要一致</strong>
                <p class="muted">质量中心、报告导出、Agent 回答使用同一份治理视图，避免前后口径冲突。</p>
              </div>
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
const summary = ref<QualitySummaryResponse | null>(null);
const submitMessage = ref('');
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
