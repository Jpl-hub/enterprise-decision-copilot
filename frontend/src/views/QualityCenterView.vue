<template>
  <div class="page-stack">
    <PagePanel title="数据质量中台" eyebrow="Quality" description="统一查看官方财报覆盖率、异常项和人工复核队列。">
      <div class="button-row">
        <button class="button-primary" @click="loadSummary">刷新质量状态</button>
      </div>
      <div v-if="loading" class="empty-state">正在加载质量摘要...</div>
      <div v-else-if="summary" class="page-stack">
        <div class="metrics-grid">
          <MetricCard label="官方财报覆盖率" :value="`${(summary.official_report_coverage_ratio * 100).toFixed(1)}%`" />
          <MetricCard label="异常企业" :value="summary.anomaly_company_count" />
          <MetricCard label="待复核" :value="summary.pending_review_count" />
          <MetricCard label="缺失槽位" :value="summary.missing_report_slots" />
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
        </div>
      </div>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { api } from '../api/client';
import type { QualitySummaryResponse } from '../api/types';
import MetricCard from '../components/MetricCard.vue';
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
