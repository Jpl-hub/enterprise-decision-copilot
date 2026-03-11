<template>
  <div class="page-stack">
    <PagePanel
      title="系统总览"
      eyebrow="Overview"
      description="聚合样本规模、企业池、风险名单和赛题演示入口。"
    >
      <div v-if="store.loading" class="empty-state">正在加载系统总览...</div>
      <div v-else-if="store.error" class="error-box">{{ store.error }}</div>
      <template v-else-if="store.payload">
        <div class="metrics-grid" v-if="store.payload.metrics">
          <MetricCard label="样本企业" :value="store.payload.metrics.sample_count" />
          <MetricCard label="平均综合评分" :value="store.payload.metrics.avg_score" :hint="`${store.payload.metrics.latest_year} 年`" />
          <MetricCard label="个股研报" :value="store.payload.metrics.research_report_count" />
          <MetricCard label="行业研报" :value="store.payload.metrics.industry_report_count" />
        </div>
        <div class="metrics-grid" v-if="warehouse?.warehouse_ready">
          <MetricCard label="DuckDB 表数" :value="warehouse.table_count" />
          <MetricCard label="最新企业行数" :value="warehouse.latest_company_rows" />
          <MetricCard label="Mart 视图" :value="warehouse.mart_views.length" />
          <MetricCard label="仓库状态" :value="warehouse.warehouse_ready ? 'Ready' : 'Pending'" />
        </div>
        <div class="metrics-grid" v-if="riskModel">
          <MetricCard label="风险模型" :value="riskModel.model_ready ? 'Ready' : 'Pending'" />
          <MetricCard label="训练样本" :value="riskModel.sample_count" />
          <MetricCard label="高风险样本" :value="riskModel.positive_samples" />
          <MetricCard label="ROC AUC" :value="formatMetric(riskModel.metrics.roc_auc)" />
        </div>
        <div class="metrics-grid" v-if="universe?.universe_ready">
          <MetricCard label="行业公司池" :value="universe.company_count" />
          <MetricCard label="覆盖子行业" :value="universe.industry_count" />
          <MetricCard label="候选研报量" :value="universe.total_report_count" />
          <MetricCard label="目标池重合" :value="universe.target_overlap_count" />
        </div>
        <div class="metrics-grid" v-if="universe?.financial_readiness">
          <MetricCard label="扩容财务就绪" :value="universe.financial_readiness.ready_candidate_count" />
          <MetricCard label="部分就绪" :value="universe.financial_readiness.partial_candidate_count" />
          <MetricCard label="官方特征公司" :value="universe.financial_readiness.official_feature_company_count" />
          <MetricCard label="年报覆盖率" :value="`${(universe.financial_readiness.average_year_coverage_ratio * 100).toFixed(1)}%`" />
        </div>
        <div class="metrics-grid" v-if="promotionPlan?.plan_ready">
          <MetricCard label="扩容候选数" :value="promotionPlan.candidate_count" />
          <MetricCard label="入选计划数" :value="promotionPlan.selected_count" />
          <MetricCard label="单赛道上限" :value="promotionPlan.per_industry_limit" />
          <MetricCard label="计划覆盖赛道" :value="promotionPlan.industries.length" />
        </div>
        <div class="panel-split three-cols" v-if="warehouse?.warehouse_ready">
          <div class="sub-panel">
            <h3>仓库企业概览</h3>
            <div class="stack-list">
              <div v-for="item in warehouse.company_overview.slice(0, 6)" :key="item.company_code" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.company_name }}</strong>
                  <span class="badge-subtle">{{ item.report_year }}</span>
                </div>
                <p class="muted">营收 {{ Number(item.revenue_million || 0).toFixed(1) }} 百万元 · 研报覆盖 {{ item.report_coverage }}</p>
              </div>
            </div>
          </div>
          <div class="sub-panel">
            <h3>行业研报热度</h3>
            <div class="stack-list">
              <div v-for="item in warehouse.industry_heat.slice(0, 6)" :key="item.industry_name" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.industry_name }}</strong>
                  <span class="badge-subtle">{{ item.report_count }}</span>
                </div>
                <p class="muted">正向 {{ item.positive_count }} · 负向 {{ item.negative_count }}</p>
              </div>
            </div>
          </div>
          <div class="sub-panel">
            <h3>企业研报覆盖</h3>
            <div class="stack-list">
              <div v-for="item in warehouse.company_research_heat.slice(0, 6)" :key="item.company_code" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.company_name }}</strong>
                  <span class="badge-subtle">{{ item.report_count }}</span>
                </div>
                <p class="muted">正向 {{ item.positive_count }} · 负向 {{ item.negative_count }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="panel-split three-cols" v-if="universe?.universe_ready">
          <div class="sub-panel">
            <h3>行业子赛道覆盖</h3>
            <div class="stack-list">
              <div v-for="item in universe.industries.slice(0, 6)" :key="item.industry_name" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.industry_name }}</strong>
                  <span class="badge-subtle">{{ item.company_count }} 家</span>
                </div>
                <p class="muted">候选研报 {{ item.report_count }} 篇</p>
              </div>
            </div>
          </div>
          <div class="sub-panel">
            <h3>扩容建议 Top</h3>
            <div class="stack-list">
              <div v-for="item in universe.recommended_candidates.slice(0, 6)" :key="item.company_code" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.company_name }}</strong>
                  <span class="badge-subtle">{{ item.candidate_priority_score.toFixed(1) }}</span>
                </div>
                <p class="muted">{{ item.industry_name }} · 研报 {{ item.report_count }} 篇 · 机构 {{ item.institution_count }} 家</p>
                <p class="muted">{{ item.recommendation_reasons.join('；') }}</p>
              </div>
            </div>
          </div>
          <div class="sub-panel">
            <h3>交易所分布</h3>
            <div class="stack-list">
              <div v-for="item in universe.exchanges" :key="item.exchange" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.exchange }}</strong>
                  <span class="badge-subtle">{{ item.company_count }} 家</span>
                </div>
                <p class="muted">候选研报 {{ item.report_count }} 篇</p>
              </div>
            </div>
          </div>
        </div>
        <div class="panel-split two-cols" v-if="promotionPlan?.plan_ready">
          <div class="sub-panel">
            <h3>平衡扩容计划</h3>
            <div class="info-card compact">
              <p class="muted">
                计划总数 {{ promotionPlan.selected_count }} 家，每个子赛道最多 {{ promotionPlan.per_industry_limit }} 家，
                目标是避免扩容名单被单一高热度赛道挤满。
              </p>
            </div>
            <div class="chip-row">
              <span v-for="item in promotionPlan.industries" :key="item.industry_name" class="badge-subtle">
                {{ item.industry_name }} {{ item.selected_count }}
              </span>
            </div>
          </div>
          <div class="sub-panel">
            <h3>计划入选企业</h3>
            <div class="candidate-grid two-cols-dense">
              <div v-for="item in promotionPlan.candidates.slice(0, 8)" :key="item.company_code" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.company_name }}</strong>
                  <span class="badge-subtle">{{ item.candidate_priority_score.toFixed(1) }}</span>
                </div>
                <p class="muted">{{ item.industry_name }} · {{ item.exchange }} · 研报 {{ item.report_count }} 篇</p>
                <p class="muted">{{ item.recommendation_reasons.join('；') }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="panel-split two-cols" v-if="universe?.financial_readiness?.promotion_candidate_count">
          <div class="sub-panel">
            <h3>扩容财务就绪度</h3>
            <div class="info-card compact">
              <p class="muted">
                已纳入扩容计划 {{ universe.financial_readiness.promotion_candidate_count }} 家，其中三年官方财务特征齐备
                {{ universe.financial_readiness.ready_candidate_count }} 家，部分齐备 {{ universe.financial_readiness.partial_candidate_count }} 家。
              </p>
            </div>
            <div class="chip-row">
              <span class="badge-subtle">三年齐备 {{ universe.financial_readiness.ready_candidate_count }}</span>
              <span class="badge-subtle">部分齐备 {{ universe.financial_readiness.partial_candidate_count }}</span>
              <span class="badge-subtle">待补齐 {{ universe.financial_readiness.pending_candidate_count }}</span>
            </div>
          </div>
          <div class="sub-panel">
            <h3>就绪候选企业</h3>
            <div class="candidate-grid two-cols-dense">
              <div v-for="item in universe.financial_readiness.candidates" :key="item.company_code" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.company_name }}</strong>
                  <span class="badge-subtle">{{ item.readiness_status }}</span>
                </div>
                <p class="muted">{{ item.industry_name }} · {{ item.exchange }} · 优先级 {{ item.candidate_priority_score.toFixed(1) }}</p>
                <p class="muted">年报年份 {{ item.report_years.join(' / ') || '待补齐' }} · 覆盖 {{ (item.year_coverage_ratio * 100).toFixed(0) }}%</p>
              </div>
            </div>
          </div>
        </div>
        <div class="sub-panel" v-if="universe?.universe_ready">
          <h3>候选企业观察池</h3>
          <div class="candidate-grid">
            <div v-for="item in universe.top_companies.slice(0, 8)" :key="item.company_code" class="info-card compact">
              <div class="trace-title-row">
                <strong>{{ item.company_name }}</strong>
                <span class="badge-subtle">{{ item.exchange }}</span>
              </div>
              <p class="muted">{{ item.industry_name }} · 研报 {{ item.report_count }} 篇 · 机构 {{ item.institution_count }} 家</p>
              <p class="muted">{{ item.in_target_pool ? '已进入正式目标池' : '候选扩展企业' }}</p>
            </div>
          </div>
        </div>
        <div class="panel-split two-cols" v-if="riskModel">
          <div class="sub-panel">
            <h3>AI 风险模型概览</h3>
            <div class="info-card compact">
              <p class="muted">
                模型类型 {{ riskModel.model_type || '未训练' }}，最近训练时间 {{ riskModel.trained_at || '暂无' }}。
                当前使用 CPU 友好的表格分类模型，作为规则风险引擎的第二判断层。
              </p>
            </div>
            <div class="info-card compact">
              <strong>评估指标</strong>
              <p class="muted">
                Accuracy {{ formatMetric(riskModel.metrics.accuracy) }} ·
                Precision {{ formatMetric(riskModel.metrics.precision) }} ·
                Recall {{ formatMetric(riskModel.metrics.recall) }} ·
                F1 {{ formatMetric(riskModel.metrics.f1) }}
              </p>
            </div>
          </div>
          <div class="sub-panel">
            <div class="sub-panel-header">
              <h3>目标企业池</h3>
              <RouterLink to="/workbench">进入企业工作台</RouterLink>
            </div>
            <div class="card-grid two-cols">
              <div v-for="item in store.payload.targets" :key="item.company_code" class="info-card">
                <span class="badge-subtle">{{ item.exchange }}</span>
                <h3>{{ item.company_name }}</h3>
                <p class="muted">{{ item.segment }}</p>
                <div class="button-row">
                  <RouterLink class="button-ghost" to="/compare">对比</RouterLink>
                  <RouterLink class="button-ghost" :to="`/workbench/${item.company_code}`">分析</RouterLink>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="panel-split" v-if="!riskModel">
          <div class="sub-panel">
            <div class="sub-panel-header">
              <h3>目标企业池</h3>
              <RouterLink to="/workbench">进入企业工作台</RouterLink>
            </div>
            <div class="card-grid two-cols">
              <div v-for="item in store.payload.targets" :key="item.company_code" class="info-card">
                <span class="badge-subtle">{{ item.exchange }}</span>
                <h3>{{ item.company_name }}</h3>
                <p class="muted">{{ item.segment }}</p>
                <div class="button-row">
                  <RouterLink class="button-ghost" to="/compare">对比</RouterLink>
                  <RouterLink class="button-ghost" :to="`/workbench/${item.company_code}`">分析</RouterLink>
                </div>
              </div>
            </div>
          </div>
          <div class="sub-panel">
            <div class="sub-panel-header">
              <h3>风险关注</h3>
              <RouterLink to="/quality">查看质量中台</RouterLink>
            </div>
            <div class="stack-list">
              <div v-for="item in store.payload.watchlist" :key="String(item.company_code)" class="info-card compact">
                <div class="trace-title-row">
                  <strong>{{ item.company_name }}</strong>
                  <span class="badge-subtle">{{ item.risk_level }}风险</span>
                </div>
                <p class="muted">{{ Array.isArray(item.risk_flags) ? item.risk_flags.join('；') : '暂无风险标记' }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="sub-panel" v-else>
          <div class="sub-panel-header">
            <h3>风险关注</h3>
            <RouterLink to="/quality">查看质量中台</RouterLink>
          </div>
          <div class="stack-list">
            <div v-for="item in store.payload.watchlist" :key="String(item.company_code)" class="info-card compact">
              <div class="trace-title-row">
                <strong>{{ item.company_name }}</strong>
                <span class="badge-subtle">{{ item.risk_level }}风险</span>
              </div>
              <p class="muted">{{ Array.isArray(item.risk_flags) ? item.risk_flags.join('；') : '暂无风险标记' }}</p>
            </div>
          </div>
        </div>
      </template>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';

import { api } from '../api/client';
import type { RiskModelSummaryResponse, UniversePromotionPlanResponse, UniverseSummaryResponse, WarehouseOverviewResponse } from '../api/types';
import MetricCard from '../components/MetricCard.vue';
import PagePanel from '../components/PagePanel.vue';
import { useDashboardStore } from '../stores/dashboard';

const store = useDashboardStore();
const warehouse = ref<WarehouseOverviewResponse | null>(null);
const riskModel = ref<RiskModelSummaryResponse | null>(null);
const universe = ref<UniverseSummaryResponse | null>(null);
const promotionPlan = ref<UniversePromotionPlanResponse | null>(null);

function formatMetric(value: number | null | undefined) {
  return value == null ? '暂无' : value.toFixed(3);
}

onMounted(async () => {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  const [warehouseResult, riskModelResult, universeResult, promotionPlanResult] = await Promise.all([
    api.getWarehouseOverview(),
    api.getRiskModelSummary(),
    api.getUniverseSummary(),
    api.getUniversePromotionPlan(),
  ]);
  warehouse.value = warehouseResult;
  riskModel.value = riskModelResult;
  universe.value = universeResult;
  promotionPlan.value = promotionPlanResult;
});
</script>
