<template>
  <div class="board-page">
    <div class="board-shell">
      <header class="board-hero">
        <div class="board-hero-copy">
          <span class="board-kicker">决策态势屏</span>
          <h1>企业运营态势总览</h1>
          <p>
            面向项目展示与集中研判，统一呈现企业池状态、披露进度、风险关注与宏观脉冲。
          </p>
        </div>
        <div class="board-hero-actions">
          <RouterLink to="/" class="board-btn subtle">返回分析中枢</RouterLink>
          <RouterLink v-if="leaderCode" :to="`/workbench/${leaderCode}`" class="board-btn solid">进入领先标的分析</RouterLink>
        </div>
      </header>

      <section class="board-metric-strip" v-if="headlineMetrics.length">
        <article v-for="item in headlineMetrics" :key="item.label" class="board-metric-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.detail }}</p>
        </article>
      </section>

      <section class="board-main-grid">
        <article class="board-panel board-leader-panel">
          <div class="board-panel-head">
            <span>当前领先标的</span>
            <RouterLink v-if="leaderCode" :to="`/workbench/${leaderCode}`">查看详情</RouterLink>
          </div>
          <div class="board-leader-core" v-if="leader">
            <strong>{{ leader.company_name }}</strong>
            <div class="board-leader-score">{{ formatNumber(leader.total_score, 1) }}</div>
            <p>
              风险等级 {{ leader.risk_level || '待评估' }}，当前在目标企业池中综合表现领先。
            </p>
          </div>
          <div v-else class="board-empty">当前暂无可展示的领先企业。</div>
        </article>

        <article class="board-panel board-risk-panel">
          <div class="board-panel-head">
            <span>风险关注</span>
            <RouterLink to="/quality">查看治理状态</RouterLink>
          </div>
          <div class="board-risk-list" v-if="watchlist.length">
            <div v-for="item in watchlist" :key="item.company_code" class="board-risk-item">
              <div>
                <strong>{{ item.company_name }}</strong>
                <p>{{ item.risk_level || '待评估' }}风险</p>
              </div>
              <div class="board-risk-tags">
                <span v-for="flag in item.risk_flags.slice(0, 2)" :key="flag">{{ flag }}</span>
              </div>
            </div>
          </div>
          <div v-else class="board-empty">风险观察列表同步中。</div>
        </article>
      </section>

      <section class="board-dual-grid">
        <article class="board-panel">
          <div class="board-panel-head">
            <span>披露进度</span>
            <span>{{ freshness?.latest_periodic_label || '年报口径' }}</span>
          </div>
          <div v-if="periodSummaries.length" class="board-progress-list">
            <div v-for="item in periodSummaries" :key="item.period_type" class="board-progress-item">
              <div class="board-progress-top">
                <strong>{{ item.period_label }}</strong>
                <span>{{ item.covered_companies }}/{{ targetCount }}</span>
              </div>
              <div class="board-progress-track">
                <div class="board-progress-fill" :style="{ width: `${Math.max(8, item.coverage_ratio * 100)}%` }"></div>
              </div>
              <p>{{ item.latest_company_name || '最新披露企业同步中' }} · {{ item.latest_published_at || '日期同步中' }}</p>
            </div>
          </div>
          <div v-else class="board-empty">披露进度同步中。</div>
        </article>

        <article class="board-panel">
          <div class="board-panel-head">
            <span>宏观脉冲</span>
            <span>{{ latestMacroPeriod || '最新周期同步中' }}</span>
          </div>
          <div v-if="macroCards.length" class="board-macro-grid">
            <div v-for="item in macroCards" :key="item.title" class="board-macro-card">
              <span>{{ item.title }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
          <div v-else class="board-empty">宏观指标同步中。</div>
        </article>
      </section>

      <section class="board-dual-grid">
        <article class="board-panel">
          <div class="board-panel-head">
            <span>企业排序</span>
            <RouterLink to="/compare">进入企业对比</RouterLink>
          </div>
          <div v-if="ranking.length" class="board-ranking-list">
            <div v-for="item in ranking" :key="item.company_code" class="board-ranking-item">
              <div class="board-ranking-rank">{{ item.rank }}</div>
              <div class="board-ranking-main">
                <strong>{{ item.company_name }}</strong>
                <p>{{ item.risk_level || '待评估' }}风险</p>
              </div>
              <div class="board-ranking-score">{{ formatNumber(item.total_score, 1) }}</div>
            </div>
          </div>
          <div v-else class="board-empty">企业排序同步中。</div>
        </article>

        <article class="board-panel">
          <div class="board-panel-head">
            <span>态势动作</span>
            <span>推荐下一步</span>
          </div>
          <div class="board-action-stack">
            <RouterLink v-if="leaderCode" :to="`/competition/${leaderCode}`" class="board-action-card">
              <strong>导出领先标的材料</strong>
              <p>快速生成当前优势企业的正式分析材料与证据清单。</p>
            </RouterLink>
            <RouterLink to="/compare" class="board-action-card">
              <strong>发起双企业比较</strong>
              <p>基于当前企业池，继续完成横向判断与差异拆解。</p>
            </RouterLink>
            <RouterLink to="/quality" class="board-action-card">
              <strong>查看数据可信状态</strong>
              <p>检查来源、覆盖、检索评测与待复核事项。</p>
            </RouterLink>
          </div>
        </article>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import { useDashboardStore } from '../stores/dashboard';

const store = useDashboardStore();

type RankingItem = {
  company_code: string;
  company_name: string;
  total_score: number;
  risk_level?: string;
};

type WatchItem = {
  company_code: string;
  company_name: string;
  risk_level?: string;
  risk_flags: string[];
};

type MacroItem = {
  indicator_name?: string;
  indicator_value?: string | number;
  unit?: string;
  period?: string;
};

const payload = computed(() => store.payload);
const freshness = computed(() => payload.value?.freshness || null);
const targetCount = computed(() => store.targets.length);
const ranking = computed(() =>
  ((payload.value?.ranking || []) as RankingItem[]).slice(0, 6).map((item, index) => ({
    ...item,
    rank: index + 1,
  })),
);
const watchlist = computed(() => ((payload.value?.watchlist || []) as WatchItem[]).slice(0, 4));
const macroItems = computed(() => ((payload.value?.macro || []) as MacroItem[]).slice(0, 4));
const leader = computed(() => ranking.value[0] || null);
const leaderCode = computed(() => leader.value?.company_code || '');
const latestMacroPeriod = computed(() => freshness.value?.latest_macro_period || '');
const periodSummaries = computed(() => freshness.value?.period_summaries || []);

const headlineMetrics = computed(() => {
  const metrics = payload.value?.metrics;
  if (!metrics) return [];
  return [
    {
      label: '目标企业',
      value: `${metrics.sample_count} 家`,
      detail: '当前已进入统一分析池的企业数量。',
    },
    {
      label: '研究证据',
      value: `${metrics.research_report_count + metrics.industry_report_count} 条`,
      detail: '来自个股研报与行业研究的证据规模。',
    },
    {
      label: '平均赋分',
      value: metrics.avg_score.toFixed(1),
      detail: '当前目标池整体经营状态基线。',
    },
    {
      label: '最新披露',
      value: freshness.value?.latest_official_disclosure || '同步中',
      detail: freshness.value?.latest_periodic_label || '定期披露口径',
    },
  ];
});

const macroCards = computed(() =>
  macroItems.value.map((item) => ({
    title: item.indicator_name || '宏观指标',
    value: `${item.indicator_value ?? '--'}${item.unit ?? ''}`,
  })),
);

function formatNumber(value: number | string | null | undefined, digits = 1) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '--';
  return num.toFixed(digits);
}

onMounted(async () => {
  if (!store.payload && !store.loading) {
    await store.load();
  }
});
</script>

<style scoped>
.board-page {
  min-height: calc(100vh - 96px);
  margin: -28px;
  padding: 32px;
  background:
    radial-gradient(circle at top left, rgba(57, 255, 20, 0.12), transparent 22%),
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.16), transparent 28%),
    linear-gradient(180deg, #07111b 0%, #081420 46%, #091826 100%);
}

.board-shell {
  max-width: 1680px;
  margin: 0 auto;
  display: grid;
  gap: 22px;
}

.board-hero,
.board-panel,
.board-metric-card {
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(7, 17, 27, 0.72);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(18px);
}

.board-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) auto;
  gap: 24px;
  align-items: end;
  padding: 30px 34px;
  border-radius: 28px;
}

.board-kicker {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(57, 255, 20, 0.12);
  border: 1px solid rgba(57, 255, 20, 0.26);
  color: #c7ffbc;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.board-hero h1 {
  margin: 16px 0 12px;
  font-family: 'Syne', 'DM Sans', sans-serif;
  font-size: clamp(42px, 5vw, 68px);
  line-height: 1.02;
  letter-spacing: -0.05em;
  color: #f8fafc;
}

.board-hero p {
  margin: 0;
  max-width: 760px;
  font-size: 16px;
  line-height: 1.8;
  color: rgba(226, 232, 240, 0.78);
}

.board-hero-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.board-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 0 18px;
  border-radius: 999px;
  font-weight: 700;
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.board-btn:hover {
  transform: translateY(-1px);
}

.board-btn.solid {
  background: linear-gradient(135deg, #39ff14, #97ff84);
  color: #04110c;
  box-shadow: 0 14px 34px rgba(57, 255, 20, 0.18);
}

.board-btn.subtle {
  background: rgba(255, 255, 255, 0.04);
  color: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.board-metric-strip,
.board-main-grid,
.board-dual-grid {
  display: grid;
  gap: 18px;
}

.board-metric-strip {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.board-metric-card {
  padding: 20px 22px;
  border-radius: 22px;
}

.board-metric-card span,
.board-panel-head span:first-child,
.board-progress-top span,
.board-risk-item p {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.82);
}

.board-metric-card strong {
  display: block;
  margin-top: 10px;
  font-family: 'Syne', 'DM Sans', sans-serif;
  font-size: clamp(24px, 2.2vw, 34px);
  line-height: 1.08;
  color: #f8fafc;
}

.board-metric-card p {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(226, 232, 240, 0.7);
}

.board-main-grid {
  grid-template-columns: minmax(0, 1.2fr) minmax(340px, 0.8fr);
}

.board-dual-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.board-panel {
  padding: 24px;
  border-radius: 26px;
}

.board-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 20px;
}

.board-panel-head a,
.board-panel-head span:last-child {
  font-size: 13px;
  color: rgba(148, 163, 184, 0.86);
}

.board-leader-core {
  display: grid;
  gap: 10px;
}

.board-leader-core strong {
  font-size: clamp(28px, 3vw, 42px);
  line-height: 1.05;
  color: #f8fafc;
}

.board-leader-score {
  font-family: 'Syne', 'DM Sans', sans-serif;
  font-size: clamp(60px, 8vw, 112px);
  line-height: 0.95;
  letter-spacing: -0.06em;
  color: #39ff14;
}

.board-leader-core p,
.board-empty,
.board-progress-item p,
.board-action-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: rgba(226, 232, 240, 0.72);
}

.board-risk-list,
.board-progress-list,
.board-ranking-list,
.board-action-stack {
  display: grid;
  gap: 14px;
}

.board-risk-item,
.board-ranking-item,
.board-action-card {
  display: grid;
  gap: 10px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.board-risk-item {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.board-risk-item strong,
.board-ranking-main strong,
.board-action-card strong {
  display: block;
  color: #f8fafc;
  font-size: 16px;
}

.board-risk-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.board-risk-tags span {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(239, 68, 68, 0.14);
  border: 1px solid rgba(248, 113, 113, 0.2);
  color: #fecaca;
  font-size: 12px;
  font-weight: 700;
}

.board-progress-item {
  display: grid;
  gap: 10px;
}

.board-progress-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.board-progress-top strong {
  color: #f8fafc;
}

.board-progress-track {
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
}

.board-progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #39ff14, #1d4ed8);
}

.board-macro-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.board-macro-card {
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.84), rgba(15, 23, 42, 0.58));
  border: 1px solid rgba(96, 165, 250, 0.16);
}

.board-macro-card span {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(191, 219, 254, 0.8);
}

.board-macro-card strong {
  font-family: 'Syne', 'DM Sans', sans-serif;
  font-size: 28px;
  line-height: 1.05;
  color: #eff6ff;
}

.board-ranking-item {
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
}

.board-ranking-rank {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(57, 255, 20, 0.12);
  color: #d9ffcf;
  font-weight: 800;
}

.board-ranking-main p {
  margin: 4px 0 0;
}

.board-ranking-score {
  font-family: 'DM Mono', monospace;
  font-size: 22px;
  color: #f8fafc;
}

.board-action-card {
  text-decoration: none;
}

.board-action-card:hover {
  border-color: rgba(57, 255, 20, 0.24);
  transform: translateY(-1px);
}

@media (max-width: 1200px) {
  .board-metric-strip,
  .board-main-grid,
  .board-dual-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .board-page {
    margin: -28px -16px;
    padding: 18px 16px 32px;
  }

  .board-hero {
    grid-template-columns: 1fr;
    padding: 22px;
  }

  .board-macro-grid {
    grid-template-columns: 1fr;
  }
}
</style>
