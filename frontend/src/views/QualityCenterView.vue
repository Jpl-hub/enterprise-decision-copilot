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
              <span>核心样本</span>
              <strong>{{ summary.target_pool_ready ? '已就绪' : '未完成' }}</strong>
              <div class="signal-meter"><div class="signal-meter-fill" :style="{ width: `${summary.official_report_coverage_ratio * 100}%` }"></div></div>
            </div>
            <div class="tower-stat-card">
              <span>扩展样本</span>
              <strong>{{ summary.universe_report_downloaded_slots }}/{{ summary.universe_report_expected_slots }}</strong>
              <div class="signal-meter"><div class="signal-meter-fill accent" :style="{ width: `${summary.multimodal_extract_coverage_ratio * 100}%` }"></div></div>
            </div>
            <div class="tower-stat-card warning">
              <span>图表补全</span>
              <strong>{{ summary.multimodal_extract_report_count }}/{{ summary.multimodal_expected_report_count }}</strong>
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
            <span>扩展样本</span>
            <strong>{{ summary.universe_report_downloaded_slots }}/{{ summary.universe_report_expected_slots }}</strong>
            <p>扩展企业池的年报下载进度，决定后续可扩到多大范围。</p>
          </div>
          <div class="flow-arrow">→</div>
          <div class="flow-card">
            <span>图表补全</span>
            <strong>{{ summary.multimodal_extract_report_count }}/{{ summary.multimodal_expected_report_count }}</strong>
            <p>复杂图表和表格是否已经补成结构化证据。</p>
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
              <h3>当前缺口</h3>
              <span class="badge-subtle">先看这些</span>
            </div>
            <div class="stack-list">
              <div class="anomaly-heat-card">
                <div class="trace-title-row">
                  <strong>缺报告</strong>
                  <span>{{ summary.issue_breakdown.missing_reports }} 项</span>
                </div>
                <p>主样本或扩展样本里，仍未下载到位的官方年报。</p>
              </div>
              <div class="anomaly-heat-card">
                <div class="trace-title-row">
                  <strong>字段缺口</strong>
                  <span>{{ summary.issue_breakdown.field_gaps }} 项</span>
                </div>
                <p>关键字段缺失或版式异常，可能影响经营与风险判断。</p>
              </div>
              <div class="anomaly-heat-card">
                <div class="trace-title-row">
                  <strong>图表待补</strong>
                  <span>{{ summary.issue_breakdown.multimodal_missing }} 项</span>
                </div>
                <p>已下载年报但还没有完成图表与表格补全。</p>
              </div>
              <div class="anomaly-heat-card">
                <div class="trace-title-row">
                  <strong>图表偏少</strong>
                  <span>{{ summary.issue_breakdown.multimodal_low_coverage }} 项</span>
                </div>
                <p>已做图表补全，但识别字段仍然偏少。</p>
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
  if (!summary.value.target_pool_ready) return '核心样本还没有全部就绪';
  if (summary.value.multimodal_extract_coverage_ratio < 0.5) return '核心样本可用，但图表补全还没有做完';
  if (summary.value.universe_report_coverage_ratio < 0.9) return '核心样本可用，扩展样本仍在补齐';
  return '数据底座已进入稳定运行';
  return '数据底座正在持续扩充';
});

const readinessText = computed(() => {
  if (!summary.value) return '正在汇总';
  return `核心样本 ${summary.value.official_report_downloaded_slots}/${summary.value.official_report_expected_slots}，扩展样本 ${summary.value.universe_report_downloaded_slots}/${summary.value.universe_report_expected_slots}，图表补全 ${summary.value.multimodal_extract_report_count}/${summary.value.multimodal_expected_report_count}。`;
});

const confidenceNotes = computed(() => {
  if (!summary.value) return [];
  const notes = [
    `核心样本已覆盖 ${summary.value.official_report_downloaded_slots}/${summary.value.official_report_expected_slots}，主分析链路可以先围绕这些企业展开。`,
    `扩展样本当前是 ${summary.value.universe_report_downloaded_slots}/${summary.value.universe_report_expected_slots}，后续大范围对比还要继续补齐。`,
  ];
  if (summary.value.multimodal_extract_coverage_ratio < 0.5) {
    notes.push('图表补全还不够，遇到复杂图表型问题时需要谨慎引用。');
  } else if (summary.value.universe_report_coverage_ratio < 0.9) {
    notes.push('主样本可用，但扩展企业池还没有完全补齐。');
  } else {
    notes.push('核心样本、扩展样本和图表补全都已进入可用区间。');
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
