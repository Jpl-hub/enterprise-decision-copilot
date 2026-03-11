<template>
  <div class="page-stack">
    <PagePanel title="企业对比驾驶舱" eyebrow="Compare" description="基于真实财报、研报和趋势证据，对多家企业做横向评估与维度拆解。">
      <div class="panel-split two-cols">
        <div class="sub-panel">
          <div class="sub-panel-header">
            <h3>选择企业</h3>
            <span class="badge-subtle">至少 2 家，最多 4 家</span>
          </div>
          <div class="compare-target-grid">
            <label
              v-for="item in targets"
              :key="item.company_code"
              class="compare-target-card"
              :class="{ active: selectedCodes.includes(item.company_code) }"
            >
              <input
                type="checkbox"
                :checked="selectedCodes.includes(item.company_code)"
                @change="toggleCompany(item.company_code)"
              />
              <div>
                <strong>{{ item.company_name }}</strong>
                <p class="muted">{{ item.exchange }} · {{ item.segment }}</p>
              </div>
            </label>
          </div>
          <div class="button-row">
            <button class="button-primary" @click="loadComparison" :disabled="selectedCodes.length < 2 || loading">开始对比</button>
            <button class="button-ghost" @click="resetSelection">重置为默认组合</button>
          </div>
        </div>
        <div class="sub-panel">
          <h3>对比说明</h3>
          <div class="stack-list">
            <div class="info-card compact">
              <strong>评估维度</strong>
              <p class="muted">综合表现、盈利能力、成长性、创新投入、经营韧性、风险水平。</p>
            </div>
            <div class="info-card compact">
              <strong>证据来源</strong>
              <p class="muted">交易所年报、个股研报、行业研报和多年度趋势摘要，不使用无出处结论。</p>
            </div>
            <div class="info-card compact">
              <strong>当前选择</strong>
              <p class="muted">{{ selectedCompanyNames.join('、') || '未选择企业' }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="selectedCodes.length < 2" class="empty-state">先选择至少两家企业，再生成横向对比。</div>
      <div v-else-if="loading" class="empty-state">正在生成多企业对比结论...</div>
      <div v-else-if="error" class="error-box">{{ error }}</div>
      <div v-else-if="result" class="page-stack">
        <div class="metrics-grid">
          <MetricCard label="对比企业数" :value="result.comparison_rows.length" />
          <MetricCard label="领先企业" :value="result.winner_company_name" :hint="`${result.report_year} 年`" />
          <MetricCard label="胜出维度" :value="winnerDimensionCount" />
          <MetricCard label="高亮结论" :value="result.highlights.length" />
        </div>

        <div class="panel-split two-cols">
          <div class="sub-panel">
            <h3>综合结论</h3>
            <div class="info-card compact compare-hero-card">
              <p class="section-tag">Leader</p>
              <h3>{{ result.winner_company_name }}</h3>
              <p class="muted">{{ result.summary }}</p>
            </div>
            <div class="stack-list">
              <div v-for="item in result.highlights" :key="item" class="info-card compact">
                <p class="muted">{{ item }}</p>
              </div>
            </div>
          </div>
          <div class="sub-panel">
            <h3>企业横向快照</h3>
            <div class="stack-list">
              <div v-for="item in result.comparison_rows" :key="item.company_code" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.company_name }}</strong>
                  <span class="badge-subtle">{{ item.total_score.toFixed(1) }} 分</span>
                </div>
                <p class="muted">
                  风险 {{ item.risk_level }} · 营收 {{ formatNumber(item.revenue_million) }} 百万元 ·
                  净利润 {{ formatNumber(item.net_profit_million) }} 百万元
                </p>
                <p class="muted">
                  营收 CAGR {{ formatMetric(item.revenue_cagr_pct, '%') }} · 利润 CAGR {{ formatMetric(item.profit_cagr_pct, '%') }} ·
                  研报 {{ item.research_report_count }} 篇
                </p>
              </div>
            </div>
          </div>
        </div>

        <div class="sub-panel">
          <h3>维度拆解</h3>
          <div class="dimension-grid">
            <div v-for="dimension in result.dimensions" :key="dimension.dimension" class="info-card compact">
              <div class="trace-title-row">
                <strong>{{ dimension.dimension }}</strong>
                <span class="badge-subtle">{{ dimension.winner_company_name }}</span>
              </div>
              <p class="muted">{{ dimension.conclusion }}</p>
              <div class="dimension-rank-list">
                <div v-for="(value, index) in dimension.values" :key="`${dimension.dimension}-${value.company_code}`" class="dimension-rank-item">
                  <span>{{ index + 1 }}. {{ value.company_name }}</span>
                  <strong>{{ formatMetric(value.value) }}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="sub-panel">
          <h3>核心指标表</h3>
          <div class="compare-table">
            <div class="compare-table-row compare-table-head">
              <span>企业</span>
              <span>总分</span>
              <span>净利率</span>
              <span>ROE</span>
              <span>研发强度</span>
              <span>个股研报</span>
            </div>
            <div v-for="item in result.comparison_rows" :key="`row-${item.company_code}`" class="compare-table-row">
              <strong>{{ item.company_name }}</strong>
              <span>{{ item.total_score.toFixed(1) }}</span>
              <span>{{ formatMetric(item.net_margin_pct, '%') }}</span>
              <span>{{ formatMetric(item.roe_pct, '%') }}</span>
              <span>{{ formatMetric(item.rd_ratio_pct, '%') }}</span>
              <span>{{ item.research_report_count }}</span>
            </div>
          </div>
        </div>

        <div class="sub-panel">
          <h3>证据与溯源</h3>
          <div class="panel-split two-cols">
            <div
              v-for="company in result.evidence.companies || []"
              :key="`evidence-${company.company_code}`"
              class="info-card compact"
            >
              <div class="trace-title-row">
                <strong>{{ company.company_name }}</strong>
                <span class="badge-subtle">{{ company.company_code }}</span>
              </div>
              <p class="muted">
                趋势区间 {{ getTrendYears(company) }} · 个股研报 {{ getDigestCount(company.research_digest) }} · 行业研报 {{ getDigestCount(company.industry_digest) }}
              </p>
              <p class="muted">风险标记：{{ (company.risk_flags || []).join('；') || '暂无显著风险标记' }}</p>
              <a v-if="company.financial_source_url" :href="company.financial_source_url" target="_blank" rel="noreferrer">查看官方财报来源</a>
            </div>
          </div>
        </div>
      </div>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { api } from '../api/client';
import type { CompanyCompareResponse } from '../api/types';
import MetricCard from '../components/MetricCard.vue';
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

function formatNumber(value: number | null | undefined) {
  return value == null ? '暂无' : value.toFixed(1);
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
