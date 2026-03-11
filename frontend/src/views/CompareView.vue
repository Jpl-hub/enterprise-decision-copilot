<template>
  <div class="page-stack compare-page refined-compare-page">
    <PagePanel title="企业对比台" eyebrow="Compare Studio">
      <div class="compare-command-shell">
        <div class="compare-command-main">
          <div class="sub-panel compare-selection-panel">
            <div class="sub-panel-header">
              <h3>选择对比对象</h3>
              <span class="badge-subtle">{{ selectedCodes.length }}/4</span>
            </div>
            <div class="compare-target-grid refined-target-grid">
              <button
                v-for="item in targets"
                :key="item.company_code"
                type="button"
                class="compare-target-card refined-target-card"
                :class="{ active: selectedCodes.includes(item.company_code) }"
                @click="toggleCompany(item.company_code)"
              >
                <strong>{{ item.company_name }}</strong>
                <span>{{ item.exchange }}</span>
              </button>
            </div>
            <div class="button-row left-align top-gap">
              <button class="button-primary" @click="loadComparison" :disabled="selectedCodes.length < 2 || loading">开始对比</button>
              <button class="button-ghost" @click="resetSelection">默认组合</button>
            </div>
          </div>

          <div v-if="selectedCodes.length < 2" class="empty-state">至少选择两家企业。</div>
          <div v-else-if="loading" class="empty-state">正在生成对比结论...</div>
          <div v-else-if="error" class="error-box">{{ error }}</div>
          <div v-else-if="result" class="compare-decision-shell">
            <div class="compare-verdict-card">
              <div>
                <p class="section-tag">当前结论</p>
                <h3>{{ result.winner_company_name }}</h3>
                <p>{{ result.summary }}</p>
              </div>
              <div class="compare-verdict-stats">
                <div class="verdict-mini-stat">
                  <span>领先维度</span>
                  <strong>{{ winnerDimensionCount }}</strong>
                </div>
                <div class="verdict-mini-stat">
                  <span>对比年份</span>
                  <strong>{{ result.report_year }}</strong>
                </div>
              </div>
            </div>

            <div class="compare-chart-panel">
              <div class="sub-panel-header">
                <h3>综合分对比</h3>
                <span class="badge-subtle">越长越强</span>
              </div>
              <div class="bar-compare-list">
                <div v-for="item in result.comparison_rows" :key="item.company_code" class="bar-compare-item">
                  <div class="bar-compare-label-row">
                    <strong>{{ item.company_name }}</strong>
                    <span>{{ item.total_score.toFixed(1) }}</span>
                  </div>
                  <div class="bar-track"><div class="bar-fill" :style="{ width: scoreWidth(item.total_score) }"></div></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="result" class="compare-command-side">
          <div class="compare-action-card">
            <div class="trace-title-row">
              <strong>下一步建议</strong>
              <RouterLink :to="`/workbench/${result.winner_company_code}`">查看赢家</RouterLink>
            </div>
            <div class="stack-list">
              <div v-for="item in result.highlights.slice(0, 4)" :key="item" class="action-line-card">
                <p>{{ item }}</p>
              </div>
            </div>
          </div>
          <div class="compare-action-card">
            <div class="trace-title-row">
              <strong>当前组合</strong>
              <span class="badge-subtle">{{ selectedCompanyNames.length }} 家</span>
            </div>
            <div class="selected-pill-group">
              <span v-for="name in selectedCompanyNames" :key="name" class="selected-pill">{{ name }}</span>
            </div>
          </div>
        </div>
      </div>

      <template v-if="result">
        <div class="compare-dimension-board">
          <div v-for="dimension in result.dimensions" :key="dimension.dimension" class="dimension-board-card">
            <div class="trace-title-row">
              <strong>{{ dimension.dimension }}</strong>
              <span class="badge-subtle">{{ dimension.winner_company_name }}</span>
            </div>
            <div class="mini-bar-list top-gap">
              <div v-for="value in dimension.values" :key="`${dimension.dimension}-${value.company_code}`" class="mini-bar-item">
                <div class="mini-bar-head">
                  <span>{{ value.company_name }}</span>
                  <strong>{{ formatMetric(value.value) }}</strong>
                </div>
                <div class="mini-bar-track"><div class="mini-bar-fill" :style="{ width: dimensionWidth(dimension.values, value.value) }"></div></div>
              </div>
            </div>
            <p class="dimension-conclusion">{{ dimension.conclusion }}</p>
          </div>
        </div>

        <div class="panel-split two-cols">
          <div class="sub-panel compact-data-panel">
            <h3>关键指标</h3>
            <div class="compare-table compact-compare-table">
              <div class="compare-table-row compare-table-head">
                <span>企业</span>
                <span>净利率</span>
                <span>ROE</span>
                <span>研发强度</span>
                <span>风险</span>
              </div>
              <div v-for="item in result.comparison_rows" :key="`row-${item.company_code}`" class="compare-table-row">
                <strong>{{ item.company_name }}</strong>
                <span>{{ formatMetric(item.net_margin_pct, '%') }}</span>
                <span>{{ formatMetric(item.roe_pct, '%') }}</span>
                <span>{{ formatMetric(item.rd_ratio_pct, '%') }}</span>
                <span>{{ item.risk_level }}</span>
              </div>
            </div>
          </div>

          <div class="sub-panel compact-data-panel">
            <h3>证据入口</h3>
            <div class="stack-list">
              <div v-for="company in result.evidence.companies || []" :key="company.company_code" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ company.company_name }}</strong>
                  <span class="badge-subtle">{{ company.company_code }}</span>
                </div>
                <p>趋势区间 {{ getTrendYears(company) }} · 个股研报 {{ getDigestCount(company.research_digest) }} · 行业研报 {{ getDigestCount(company.industry_digest) }}</p>
                <a v-if="company.financial_source_url" :href="company.financial_source_url" target="_blank" rel="noreferrer">查看财报来源</a>
              </div>
            </div>
          </div>
        </div>
      </template>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';

import { api } from '../api/client';
import type { CompanyCompareResponse } from '../api/types';
import PagePanel from '../components/PagePanel.vue';
import { useDashboardStore } from '../stores/dashboard';

const MAX_SELECTION = 4;
const route = useRoute();
const router = useRouter();
const store = useDashboardStore();
const selectedCodes = ref<string[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const result = ref<CompanyCompareResponse | null>(null);

const targets = computed(() => store.targets);
const selectedCompanyNames = computed(() => targets.value.filter((item) => selectedCodes.value.includes(item.company_code)).map((item) => item.company_name));
const winnerDimensionCount = computed(() => {
  if (!result.value) return 0;
  return result.value.dimensions.filter((item) => item.winner_company_code === result.value?.winner_company_code).length;
});

function defaultCodes() {
  return targets.value.slice(0, 2).map((item) => item.company_code);
}

function formatMetric(value: number | null | undefined, suffix = '') {
  return value == null ? '暂无' : `${value.toFixed(1)}${suffix}`;
}

function getDigestCount(digest: Record<string, unknown> | undefined) {
  const count = digest?.count;
  return typeof count === 'number' ? count : 0;
}

function getTrendYears(company: NonNullable<CompanyCompareResponse['evidence']['companies']>[number]) {
  const trend = company.trend_digest || {};
  const start = trend.start_year;
  const end = trend.end_year;
  if (typeof start === 'number' && typeof end === 'number') {
    return `${start}-${end}`;
  }
  return '暂无';
}

function scoreWidth(score: number) {
  const max = Math.max(...(result.value?.comparison_rows.map((item) => item.total_score) || [1]));
  return `${Math.max(16, (score / max) * 100)}%`;
}

function dimensionWidth(values: Array<{ value: number }>, value: number) {
  const max = Math.max(...values.map((item) => item.value), 1);
  return `${Math.max(14, (value / max) * 100)}%`;
}

function syncQuery() {
  router.replace({
    query: selectedCodes.value.length ? { companies: selectedCodes.value.join(',') } : {},
  });
}

function resetSelection() {
  selectedCodes.value = defaultCodes();
  syncQuery();
  if (selectedCodes.value.length >= 2) {
    void loadComparison();
  }
}

function toggleCompany(companyCode: string) {
  const exists = selectedCodes.value.includes(companyCode);
  if (exists) {
    if (selectedCodes.value.length <= 2) return;
    selectedCodes.value = selectedCodes.value.filter((code) => code !== companyCode);
  } else {
    if (selectedCodes.value.length >= MAX_SELECTION) return;
    selectedCodes.value = [...selectedCodes.value, companyCode];
  }
  syncQuery();
}

async function ensureTargets() {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  const queryValue = typeof route.query.companies === 'string' ? route.query.companies : '';
  const queryCodes = queryValue.split(',').map((item) => item.trim()).filter(Boolean);
  selectedCodes.value = (queryCodes.length >= 2 ? queryCodes : defaultCodes()).slice(0, MAX_SELECTION);
}

async function loadComparison() {
  if (selectedCodes.value.length < 2) return;
  loading.value = true;
  error.value = null;
  try {
    result.value = await api.getCompanyCompare(selectedCodes.value);
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : '企业对比加载失败';
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await ensureTargets();
  if (selectedCodes.value.length >= 2) {
    await loadComparison();
  }
});
</script>
