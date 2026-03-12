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

          <div v-if="bootstrapping" class="empty-state">正在加载企业池与默认组合...</div>
          <div v-else-if="selectedCodes.length < 2" class="empty-state">至少选择两家企业。</div>
          <div v-else-if="loading" class="empty-state">正在生成对比结论...</div>
          <div v-else-if="error" class="error-box">{{ error }}</div>
          <template v-else-if="result">
            <div class="compare-decision-shell">
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

              <div class="compare-signal-grid">
                <div class="compare-signal-card">
                  <span>总分差</span>
                  <strong>{{ formatMetric(scoreSpread) }}</strong>
                  <p>{{ leaderRow?.company_name || '领先方' }} 相比次席的综合差距。</p>
                </div>
                <div class="compare-signal-card">
                  <span>证据总量</span>
                  <strong>{{ totalResearchCount + totalIndustryCount }}</strong>
                  <p>个股研报 {{ totalResearchCount }} · 行业研报 {{ totalIndustryCount }}</p>
                </div>
                <div class="compare-signal-card">
                  <span>最新披露</span>
                  <strong>{{ freshnessSummary?.latest_periodic_label || '年报' }}</strong>
                  <p>{{ freshnessSummary?.latest_official_disclosure || '暂无最新披露时间' }}</p>
                </div>
                <div class="compare-signal-card">
                  <span>时效锚点</span>
                  <strong>{{ freshnessSummary?.latest_stock_report || '暂无' }}</strong>
                  <p>行业更新 {{ freshnessSummary?.latest_industry_report || '暂无' }}</p>
                </div>
              </div>
            </div>

            <div class="compare-closure-strip">
              <RouterLink :to="`/workbench/${result.winner_company_code}`" class="compare-closure-link primary">
                查看赢家工作台
              </RouterLink>
              <RouterLink :to="`/competition/${result.winner_company_code}`" class="compare-closure-link">
                导出赢家材料
              </RouterLink>
              <a
                v-if="winnerEvidenceCompany?.financial_source_url"
                class="compare-closure-link"
                :href="winnerEvidenceCompany.financial_source_url"
                target="_blank"
                rel="noreferrer"
              >
                打开财报原文
              </a>
              <button type="button" class="compare-closure-link" @click="resetSelection">回到默认组合</button>
            </div>

            <div class="compare-reasoning-grid">
              <article v-for="item in reasoningCards" :key="item.title" class="compare-reasoning-card">
                <div class="trace-title-row">
                  <strong>{{ item.title }}</strong>
                  <span class="badge-subtle">{{ item.tag }}</span>
                </div>
                <p class="compare-reasoning-highlight">{{ item.highlight }}</p>
                <p>{{ item.detail }}</p>
              </article>
            </div>

            <div class="compare-chart-panel compare-story-panel">
              <div class="sub-panel-header">
                <h3>决策分野</h3>
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
              <div class="compare-spotlight-grid top-gap">
                <div v-for="item in spotlightCards" :key="item.title" class="compare-spotlight-card">
                  <div class="trace-title-row">
                    <strong>{{ item.title }}</strong>
                    <span>{{ item.companyName }}</span>
                  </div>
                  <strong class="compare-spotlight-value">{{ formatMetric(item.delta) }}</strong>
                  <p>{{ item.detail }}</p>
                </div>
              </div>
            </div>
          </template>
        </div>

        <div v-if="result" class="compare-command-side">
          <div class="compare-action-card compare-closure-card">
            <div class="trace-title-row">
              <strong>对比闭环</strong>
              <span class="badge-subtle">{{ result.winner_company_name }}</span>
            </div>
            <div class="compare-action-grid">
              <RouterLink :to="`/workbench/${result.winner_company_code}`" class="compare-action-link primary">查看赢家</RouterLink>
              <RouterLink :to="`/competition/${result.winner_company_code}`" class="compare-action-link">导出材料</RouterLink>
              <RouterLink :to="{ path: '/', query: { companies: selectedCodes.join(',') } }" class="compare-action-link">回到分析中枢</RouterLink>
              <button type="button" class="compare-action-link" @click="resetSelection">默认组合</button>
            </div>
            <p class="compare-side-note">{{ closureSummary }}</p>
          </div>
          <div class="compare-action-card">
            <div class="trace-title-row">
              <strong>当前组合</strong>
              <span class="badge-subtle">{{ selectedCompanyNames.length }} 家</span>
            </div>
            <div class="selected-pill-group">
              <span v-for="name in selectedCompanyNames" :key="name" class="selected-pill">{{ name }}</span>
            </div>
            <p class="compare-side-note">{{ comboSummary }}</p>
          </div>
          <div class="compare-action-card">
            <div class="trace-title-row">
              <strong>判断基线</strong>
              <span class="badge-subtle">真实披露</span>
            </div>
            <div class="stack-list">
              <div class="action-line-card">
                <p>年报口径 {{ result.report_year }}，最新定期披露 {{ freshnessSummary?.latest_periodic_label || '年报' }} {{ freshnessSummary?.latest_official_disclosure || '暂无' }}。</p>
              </div>
              <div class="action-line-card">
                <p>个股研报最新 {{ freshnessSummary?.latest_stock_report || '暂无' }}，行业研报最新 {{ freshnessSummary?.latest_industry_report || '暂无' }}。</p>
              </div>
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
                <span>营收 CAGR</span>
                <span>风险</span>
              </div>
              <div v-for="item in result.comparison_rows" :key="`row-${item.company_code}`" class="compare-table-row">
                <strong>{{ item.company_name }}</strong>
                <span>{{ formatMetric(item.net_margin_pct, '%') }}</span>
                <span>{{ formatMetric(item.roe_pct, '%') }}</span>
                <span>{{ formatMetric(item.rd_ratio_pct, '%') }}</span>
                <span>{{ formatMetric(item.revenue_cagr_pct, '%') }}</span>
                <span>{{ item.risk_level }}</span>
              </div>
            </div>
          </div>

          <div class="sub-panel compact-data-panel">
            <h3>对比快照</h3>
            <div class="stack-list">
              <div v-for="company in compareEvidenceCompanies" :key="company.company_code" class="compare-company-brief">
                <div class="trace-title-row">
                  <strong>{{ company.company_name }}</strong>
                  <span class="badge-subtle">{{ company.company_code }}</span>
                </div>
                <div class="selected-pill-group compare-company-tags">
                  <span class="selected-pill">领先维度 {{ getCompanyLeadershipCount(company.company_code) }}</span>
                  <span class="selected-pill">趋势区间 {{ getTrendYears(company) }}</span>
                  <span class="selected-pill">个股研报 {{ getDigestCount(company.research_digest) }}</span>
                  <span class="selected-pill">行业研报 {{ getDigestCount(company.industry_digest) }}</span>
                  <span class="selected-pill">多模态 {{ getMultimodalFieldCount(company) }} 项</span>
                </div>
                <p>{{ getAnnualAnchor(company) }}</p>
                <p>{{ getLatestDisclosure(company) }}</p>
                <p>{{ getMultimodalSummary(company) }}</p>
                <p v-if="company.risk_flags?.length">关注：{{ company.risk_flags.join('；') }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-split two-cols">
          <div class="sub-panel compact-data-panel">
            <h3>证据流</h3>
            <div class="stack-list">
              <div v-for="company in compareEvidenceCompanies" :key="`stream-${company.company_code}`" class="compare-evidence-stream">
                <div class="trace-title-row">
                  <strong>{{ company.company_name }}</strong>
                  <span class="badge-subtle">{{ getLatestDisclosure(company) }}</span>
                </div>
                <p>个股研报：{{ getLatestTitle(company.research_digest, '暂无个股研报标题') }}</p>
                <p>行业议题：{{ getLatestTitle(company.industry_digest, '暂无行业研报标题') }}</p>
                <p>图表锚点：{{ getMultimodalSummary(company) }}</p>
                <div v-if="getMultimodalAssetLinks(company).length" class="page-anchor-row top-gap">
                  <a
                    v-for="item in getMultimodalAssetLinks(company)"
                    :key="`${company.company_code}-${item.label}-${item.url || 'missing'}`"
                    class="page-anchor-link"
                    :href="item.url || company.financial_source_url || undefined"
                    target="_blank"
                    rel="noreferrer"
                  >
                    {{ item.label }}
                  </a>
                </div>
                <a v-if="company.financial_source_url" :href="company.financial_source_url" target="_blank" rel="noreferrer">查看财报来源</a>
              </div>
            </div>
          </div>

          <div class="sub-panel compact-data-panel">
            <h3>证据入口</h3>
            <div class="stack-list">
              <div v-for="company in compareEvidenceCompanies" :key="`source-${company.company_code}`" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ company.company_name }}</strong>
                  <span class="badge-subtle">{{ getLatestResearchDate(company) || '研报待补' }}</span>
                </div>
                <p>最新行业更新 {{ getLatestIndustryDate(company) || '暂无' }} · 研究机构 {{ getLatestInstitution(company.research_digest) }}</p>
                <p>图表抽取 {{ getMultimodalFieldCount(company) }} 项 · 后端 {{ company.multimodal_digest?.backend || '待补齐' }}</p>
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
import type {
  CompareCompanyFreshnessDigest,
  CompareEvidenceCompany,
  CompareEvidenceDigest,
  CompanyCompareResponse,
  MultimodalAssetLink,
} from '../api/types';
import PagePanel from '../components/PagePanel.vue';
import { useDashboardStore } from '../stores/dashboard';

const MAX_SELECTION = 4;
const route = useRoute();
const router = useRouter();
const store = useDashboardStore();
const selectedCodes = ref<string[]>([]);
const loading = ref(false);
const bootstrapping = ref(true);
const error = ref<string | null>(null);
const result = ref<CompanyCompareResponse | null>(null);

const targets = computed(() => store.targets);
const selectedCompanyNames = computed(() => targets.value.filter((item) => selectedCodes.value.includes(item.company_code)).map((item) => item.company_name));
const comparisonRows = computed(() => result.value?.comparison_rows || []);
const compareEvidenceCompanies = computed<CompareEvidenceCompany[]>(() => result.value?.evidence.companies || []);
const leaderRow = computed(() => comparisonRows.value[0] || null);
const runnerUpRow = computed(() => comparisonRows.value[1] || null);
const winnerDimensionCount = computed(() => {
  if (!result.value) return 0;
  return result.value.dimensions.filter((item) => item.winner_company_code === result.value?.winner_company_code).length;
});
const scoreSpread = computed(() => {
  if (!leaderRow.value || !runnerUpRow.value) return 0;
  return leaderRow.value.total_score - runnerUpRow.value.total_score;
});
const totalResearchCount = computed(() => comparisonRows.value.reduce((sum, item) => sum + item.research_report_count, 0));
const totalIndustryCount = computed(() => comparisonRows.value.reduce((sum, item) => sum + item.industry_report_count, 0));
const winnerEvidenceCompany = computed(() => {
  if (!result.value) return null;
  return compareEvidenceCompanies.value.find((item) => item.company_code === result.value?.winner_company_code) || compareEvidenceCompanies.value[0] || null;
});
const totalMultimodalFieldCount = computed(() => compareEvidenceCompanies.value.reduce((sum, item) => sum + getMultimodalFieldCount(item), 0));
const spotlightCards = computed(() => {
  if (!result.value) return [];
  return result.value.dimensions
    .filter((item) => item.dimension !== '综合表现')
    .slice(0, 4)
    .map((item) => {
      const [first, second] = item.values;
      return {
        title: item.dimension,
        companyName: item.winner_company_name,
        delta: Math.abs((first?.value || 0) - (second?.value || 0)),
        detail: item.conclusion,
      };
    });
});
function getLatestSortedValue(values: string[]) {
  return values.slice().sort()[values.length - 1] || null;
}

const freshnessSummary = computed<CompareCompanyFreshnessDigest | null>(() => {
  if (!result.value) return null;
  const provided = result.value.evidence.freshness || {};
  const officialDates = compareEvidenceCompanies.value.map((item) => getOfficialDisclosureDate(item)).filter((item): item is string => Boolean(item));
  const latestStockDates = compareEvidenceCompanies.value.map((item) => getLatestResearchDate(item)).filter((item): item is string => Boolean(item));
  const latestIndustryDates = compareEvidenceCompanies.value.map((item) => getLatestIndustryDate(item)).filter((item): item is string => Boolean(item));
  return {
    annual_report_year: provided.annual_report_year ?? result.value.report_year,
    latest_official_disclosure: provided.latest_official_disclosure || getLatestSortedValue(officialDates),
    latest_periodic_label: provided.latest_periodic_label || (officialDates.length ? '年报' : null),
    latest_stock_report: provided.latest_stock_report || getLatestSortedValue(latestStockDates),
    latest_industry_report: provided.latest_industry_report || getLatestSortedValue(latestIndustryDates),
  };
});
const closureSummary = computed(() => {
  if (!result.value) return '';
  const runnerUpName = runnerUpRow.value?.company_name || '次席企业';
  return `${result.value.winner_company_name} 当前领先 ${runnerUpName} ${formatMetric(scoreSpread.value)} 分，已具备继续深挖、导出和回看原文的完整闭环。`;
});
const comboSummary = computed(() => {
  if (!result.value) return '';
  return `本轮组合覆盖 ${selectedCompanyNames.value.join('、')}，总共调用个股研报 ${totalResearchCount.value} 篇、行业研报 ${totalIndustryCount.value} 篇。`;
});
const reasoningCards = computed(() => {
  if (!result.value || !leaderRow.value) return [];
  const growthDimension = result.value.dimensions.find((item) => item.dimension === '成长性');
  const innovationDimension = result.value.dimensions.find((item) => item.dimension === '创新投入');
  const resilienceDimension = result.value.dimensions.find((item) => item.dimension === '经营韧性');
  const winnerRisk = leaderRow.value.risk_level || '待补';
  const challengerRisk = runnerUpRow.value?.risk_level || '待补';
  return [
    {
      title: '胜负判断链',
      tag: result.value.winner_company_name,
      highlight: `${result.value.winner_company_name} 领先 ${formatMetric(scoreSpread.value)} 分，拿下 ${winnerDimensionCount.value} 个维度。`,
      detail: result.value.summary,
    },
    {
      title: '增长与盈利链',
      tag: growthDimension?.winner_company_name || leaderRow.value.company_name,
      highlight: `${formatMetric(leaderRow.value.net_margin_pct, '%')} 净利率 · ${formatMetric(leaderRow.value.revenue_cagr_pct, '%')} 营收 CAGR`,
      detail: growthDimension?.conclusion || spotlightCards.value[0]?.detail || '增长与盈利结论待补充。',
    },
    {
      title: '风险与时效链',
      tag: freshnessSummary.value?.latest_periodic_label || '真实披露',
      highlight: `${leaderRow.value.company_name} 风险 ${winnerRisk}，${runnerUpRow.value?.company_name || '对手'} 风险 ${challengerRisk}。`,
      detail: `当前最新定期披露为 ${freshnessSummary.value?.latest_periodic_label || '年报'} ${freshnessSummary.value?.latest_official_disclosure || '暂无'}，个股研报最新 ${freshnessSummary.value?.latest_stock_report || '暂无'}。`,
    },
    {
      title: '证据回链',
      tag: `${compareEvidenceCompanies.value.length} 家企业`,
      highlight: `总计 ${totalResearchCount.value + totalIndustryCount.value} 条研报证据，图表抽取 ${totalMultimodalFieldCount.value} 项字段。`,
      detail: innovationDimension?.conclusion || resilienceDimension?.conclusion || '证据回链已接入财报原文、研报标题和多模态页锚点。',
    },
  ];
});

function defaultCodes() {
  return targets.value.slice(0, 2).map((item) => item.company_code);
}

function formatMetric(value: number | null | undefined, suffix = '') {
  return value == null ? '暂无' : `${value.toFixed(1)}${suffix}`;
}

function getDigestCount(digest: CompareEvidenceDigest | undefined) {
  const count = digest?.count;
  return typeof count === 'number' ? count : 0;
}

function getTrendYears(company: CompareEvidenceCompany) {
  const trend = company.trend_digest || {};
  const start = trend.start_year;
  const end = trend.end_year;
  if (typeof start === 'number' && typeof end === 'number') {
    return `${start}-${end}`;
  }
  return '暂无';
}

function getLatestTitle(digest: CompareEvidenceDigest | undefined, fallback: string) {
  const title = Array.isArray(digest?.latest_titles) ? digest?.latest_titles?.[0] : null;
  return typeof title === 'string' && title.trim() ? title : fallback;
}

function getLatestInstitution(digest: CompareEvidenceDigest | undefined) {
  const institution = Array.isArray(digest?.latest_institutions) ? digest?.latest_institutions?.[0] : null;
  return typeof institution === 'string' && institution.trim() ? institution : '暂无';
}

function getLatestRowDate(digest: CompareEvidenceDigest | undefined) {
  const row = Array.isArray(digest?.latest_rows) ? digest?.latest_rows?.[0] : null;
  const reportDate = row && typeof row === 'object' ? row.report_date : null;
  return typeof reportDate === 'string' && reportDate.trim() ? reportDate : null;
}

function extractDateFromSource(sourceUrl?: string | null) {
  if (!sourceUrl) return null;
  const normalized = sourceUrl.replace(/_/g, '-');
  const match = normalized.match(/(20\d{2})-(\d{2})-(\d{2})/) || normalized.match(/(20\d{2})(\d{2})(\d{2})/);
  if (!match) return null;
  return `${match[1]}-${match[2]}-${match[3]}`;
}

function getOfficialDisclosureDate(company: CompareEvidenceCompany) {
  return company.freshness_digest?.latest_official_disclosure
    || company.freshness_digest?.annual_report_published_at
    || company.financial_published_at
    || extractDateFromSource(company.financial_source_url);
}

function getLatestResearchDate(company: CompareEvidenceCompany) {
  return company.freshness_digest?.latest_stock_report || getLatestRowDate(company.research_digest);
}

function getLatestIndustryDate(company: CompareEvidenceCompany) {
  return company.freshness_digest?.latest_industry_report || getLatestRowDate(company.industry_digest);
}

function getAnnualAnchor(company: CompareEvidenceCompany) {
  const year = company.freshness_digest?.annual_report_year;
  const publishedAt = company.freshness_digest?.annual_report_published_at || company.financial_published_at || extractDateFromSource(company.financial_source_url);
  if (year && publishedAt) {
    return `年报口径 ${year} · 披露时间 ${publishedAt}`;
  }
  if (year) {
    return `年报口径 ${year}`;
  }
  return '年报披露时间待补充';
}

function getLatestDisclosure(company: CompareEvidenceCompany) {
  const label = company.freshness_digest?.latest_periodic_label || '年报';
  const date = getOfficialDisclosureDate(company);
  return date ? `最新披露 ${label} · ${date}` : '最新披露暂无';
}

function getCompanyLeadershipCount(companyCode: string) {
  if (!result.value) return 0;
  return result.value.dimensions.filter((item) => item.winner_company_code === companyCode).length;
}

function getMultimodalFieldCount(company: CompareEvidenceCompany) {
  return company.multimodal_digest?.filled_field_count || 0;
}

function getMultimodalSummary(company: CompareEvidenceCompany) {
  return company.multimodal_digest?.summary || '图表锚点待补齐';
}

function getMultimodalAssetLinks(company: CompareEvidenceCompany): MultimodalAssetLink[] {
  return company.multimodal_digest?.page_asset_links?.slice(0, 4) || [];
}

function scoreWidth(score: number) {
  const max = Math.max(...(result.value?.comparison_rows.map((item) => item.total_score) || [1]));
  return `${Math.max(16, (score / max) * 100)}%`;
}

function dimensionWidth(values: Array<{ value: number }>, value: number) {
  const max = Math.max(...values.map((item) => item.value), 1);
  return `${Math.max(14, (value / max) * 100)}%`;
}

function getQueryCodes() {
  const queryValue = typeof route.query.companies === 'string' ? route.query.companies : '';
  return queryValue.split(',').map((item) => item.trim()).filter(Boolean);
}

function getResolvedCodes(queryCodes: string[]) {
  const validCodes = new Set(targets.value.map((item) => item.company_code));
  const filtered = queryCodes.filter((item) => validCodes.has(item));
  if (filtered.length >= 2) {
    return filtered.slice(0, MAX_SELECTION);
  }
  return defaultCodes().slice(0, MAX_SELECTION);
}

async function waitForStoreLoad() {
  while (store.loading && !store.payload && !store.error) {
    await new Promise((resolve) => setTimeout(resolve, 80));
  }
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
  } else if (store.loading && !store.payload) {
    await waitForStoreLoad();
  }
  selectedCodes.value = getResolvedCodes(getQueryCodes());
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
  bootstrapping.value = true;
  try {
    await ensureTargets();
    if (selectedCodes.value.length >= 2) {
      await loadComparison();
    }
  } finally {
    bootstrapping.value = false;
  }
});
</script>
