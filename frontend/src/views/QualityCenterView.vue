<template>
  <div class="page-stack quality-page refined-quality-page">
    <PagePanel title="数据底座" eyebrow="Data Control Tower">
      <template #actions>
        <div class="toolbar-cluster">
          <button class="button-primary" @click="loadSummary" :disabled="loading">刷新</button>
        </div>
      </template>

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
              <span class="tower-pill">提醒 {{ summary.pending_review_count }} 项</span>
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
              <span>数据提醒</span>
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
            <span>多模态抽取</span>
            <strong>{{ summary.multimodal_extract_report_count }}/{{ summary.multimodal_expected_report_count }}</strong>
            <p>图表、表格和跨页版式补成结构化字段。</p>
          </div>
          <div class="flow-arrow">→</div>
          <div class="flow-card">
            <span>数据提醒</span>
            <strong>{{ summary.top_anomalies.length }}</strong>
            <p>自动识别覆盖缺口和字段异常，形成当前需要补齐的事项。</p>
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
                  <strong>{{ formatExchange(item.exchange) }}</strong>
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
              <h3>重点补齐企业</h3>
              <span class="badge-subtle">先看这些</span>
            </div>
            <div class="stack-list">
              <div v-for="item in summary.top_anomalies.slice(0, 5)" :key="`${item.company_code}-${item.report_year}`" class="anomaly-heat-card">
                <div class="trace-title-row">
                  <strong>{{ item.company_name }}</strong>
                  <span>{{ impactLevel(item.anomaly_score) }}</span>
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
              <h3>可信度判断</h3>
              <span class="badge-subtle">当前建议</span>
            </div>
            <div class="stack-list">
              <div v-for="item in confidenceNotes" :key="item" class="action-line-card"><p>{{ item }}</p></div>
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

const loading = ref(false);
const summary = ref<QualitySummaryResponse | null>(null);

const readinessHeadline = computed(() => {
  if (!summary.value) return '加载中';
  if (summary.value.pending_review_count >= 5) return '当前底座仍有较多资料提醒';
  if (summary.value.official_report_coverage_ratio >= 0.8) return '数据底座已进入稳定运行';
  return '数据底座正在持续扩充';
});

const readinessText = computed(() => {
  if (!summary.value) return '正在汇总';
  return `当前财报覆盖 ${percent(summary.value.official_report_coverage_ratio)}，图表抽取覆盖 ${percent(summary.value.multimodal_extract_coverage_ratio)}，数据提醒 ${summary.value.pending_review_count} 项。`;
});

const confidenceNotes = computed(() => {
  if (!summary.value) return [];
  const notes = [
    `当前财报覆盖达到 ${percent(summary.value.official_report_coverage_ratio)}，适合先从覆盖完整的企业开始分析。`,
    `图表抽取覆盖 ${percent(summary.value.multimodal_extract_coverage_ratio)}，复杂版式报告会继续补齐。`,
  ];
  if (summary.value.pending_review_count >= 5) {
    notes.push('当前资料提醒仍然较多，正式结论前建议先看最突出的缺口。');
  } else {
    notes.push('当前资料提醒较少，系统结论可以直接作为管理层讨论的起点。');
  }
  return notes;
});

const pendingWidth = computed(() => `${Math.min(100, Math.max(12, (summary.value?.pending_review_count || 0) * 10))}%`);

function percent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatExchange(value: string) {
  const labels: Record<string, string> = { SSE: '上交所', SZSE: '深交所', BSE: '北交所' };
  return labels[String(value || '').toUpperCase()] || value;
}

function impactLevel(score: number) {
  if (score >= 80) return '影响较高';
  if (score >= 50) return '需要关注';
  return '影响较低';
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

onMounted(() => {
  void loadSummary();
});
</script>
