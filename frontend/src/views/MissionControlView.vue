<template>
  <div class="mission-page">
    <div class="mission-shell">
      <header class="mission-hero">
        <div class="mission-hero-copy">
          <span class="mission-kicker">项目总控台</span>
          <h1>把数据、Agent、模型、计算和交付拉到同一个指挥面</h1>
          <p>
            这不是再加一个页面，而是把项目五条主线摆上台面。老师、评委和企业方进来之后，能直接看到现在在做什么、卡在哪里、下一步是什么。
          </p>
        </div>
        <div class="mission-hero-side" v-if="payload">
          <div class="mission-gate-badge" :class="payload.release_gate.gate_status">
            <span>发布门禁</span>
            <strong>{{ payload.release_gate.gate_status === 'open' ? '可正式推进' : '仍需复核' }}</strong>
          </div>
          <p>{{ payload.release_gate.release_note }}</p>
        </div>
      </header>

      <section class="mission-metric-strip" v-if="payload?.headline_metrics?.length">
        <article
          v-for="item in payload.headline_metrics"
          :key="item.label"
          class="mission-metric-card"
          :class="item.tone"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </section>

      <section class="mission-grid" v-if="payload">
        <article v-for="lane in payload.mission_lanes" :key="lane.lane_id" class="mission-lane-card">
          <div class="mission-lane-top">
            <div>
              <span class="mission-lane-owner">{{ lane.owner_role }}</span>
              <h3>{{ lane.name }}</h3>
            </div>
            <div class="mission-score-cluster">
              <span class="mission-status-pill" :class="lane.status">{{ statusLabel(lane.status) }}</span>
              <strong>{{ (lane.readiness_score * 100).toFixed(0) }}</strong>
            </div>
          </div>
          <p class="mission-summary">{{ lane.summary }}</p>
          <p class="mission-focus">{{ lane.current_focus }}</p>

          <div class="mission-chip-row" v-if="lane.linked_engines.length">
            <span v-for="item in lane.linked_engines" :key="item">{{ item }}</span>
          </div>

          <div class="mission-subgrid">
            <div>
              <strong>当前阻塞</strong>
              <p v-for="item in lane.blockers" :key="item">{{ item }}</p>
            </div>
            <div>
              <strong>下一步</strong>
              <p v-for="item in lane.next_actions" :key="item">{{ item }}</p>
            </div>
          </div>

          <div class="mission-deliverables">
            <span v-for="item in lane.deliverables" :key="item">{{ item }}</span>
          </div>
        </article>
      </section>

      <section class="mission-lower-grid" v-if="payload">
        <article class="mission-panel">
          <div class="mission-panel-head">
            <span>展示路线</span>
            <RouterLink to="/board">回到态势屏</RouterLink>
          </div>
          <p v-for="item in payload.showcase_flows" :key="item" class="mission-line-item">{{ item }}</p>
        </article>

        <article class="mission-panel">
          <div class="mission-panel-head">
            <span>总控台判断</span>
            <RouterLink to="/">返回分析中枢</RouterLink>
          </div>
          <p v-for="item in payload.control_tower_brief" :key="item" class="mission-line-item">{{ item }}</p>
        </article>
      </section>

      <div v-if="loading" class="mission-empty">正在加载项目总控台...</div>
      <div v-else-if="error" class="mission-empty danger">{{ error }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { api } from '../api/client';
import type { AIMissionControlResponse } from '../api/types';

const payload = ref<AIMissionControlResponse | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

function statusLabel(status: string) {
  if (status === 'active') return '运行中';
  if (status === 'building') return '建设中';
  return '预热中';
}

onMounted(async () => {
  loading.value = true;
  error.value = null;
  try {
    payload.value = await api.getAIMissionControl();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载项目总控台失败';
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.mission-page {
  min-height: calc(100vh - 96px);
  margin: -28px;
  padding: 28px;
  background:
    radial-gradient(circle at top left, rgba(34, 197, 94, 0.11), transparent 24%),
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 22%),
    linear-gradient(180deg, #f4f7fb 0%, #eef3f8 52%, #f8fafc 100%);
}

.mission-shell {
  max-width: 1680px;
  margin: 0 auto;
  display: grid;
  gap: 20px;
}

.mission-hero,
.mission-lane-card,
.mission-panel,
.mission-metric-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 22px 54px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(16px);
}

.mission-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(280px, 0.55fr);
  gap: 24px;
  padding: 30px 34px;
  border-radius: 30px;
}

.mission-kicker {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(15, 23, 42, 0.08);
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.mission-hero h1 {
  margin: 16px 0 12px;
  font-family: 'Syne', 'DM Sans', sans-serif;
  font-size: clamp(40px, 4.6vw, 66px);
  line-height: 1.04;
  letter-spacing: -0.05em;
  color: #0f172a;
}

.mission-hero p,
.mission-summary,
.mission-focus,
.mission-line-item,
.mission-subgrid p {
  margin: 0;
  font-size: 15px;
  line-height: 1.8;
  color: #475569;
}

.mission-hero-side {
  display: grid;
  gap: 14px;
  align-content: start;
}

.mission-gate-badge {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(135deg, #0f172a, #1e293b);
  color: #f8fafc;
}

.mission-gate-badge.review_required {
  background: linear-gradient(135deg, #7c2d12, #b45309);
}

.mission-gate-badge span {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.72);
}

.mission-gate-badge strong {
  font-size: 22px;
  line-height: 1.1;
}

.mission-metric-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
}

.mission-metric-card {
  display: grid;
  gap: 8px;
  padding: 18px 20px;
  border-radius: 22px;
}

.mission-metric-card.warning {
  background: rgba(255, 247, 237, 0.92);
}

.mission-metric-card span {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
  font-weight: 700;
}

.mission-metric-card strong {
  font-family: 'Syne', 'DM Sans', sans-serif;
  font-size: clamp(22px, 2vw, 30px);
  line-height: 1.08;
  color: #0f172a;
}

.mission-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.mission-lane-card {
  display: grid;
  gap: 16px;
  padding: 24px;
  border-radius: 28px;
}

.mission-lane-top {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: start;
}

.mission-lane-owner {
  display: inline-flex;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

.mission-lane-top h3 {
  margin: 0;
  font-size: 28px;
  line-height: 1.1;
  color: #0f172a;
}

.mission-score-cluster {
  display: grid;
  justify-items: end;
  gap: 8px;
}

.mission-status-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mission-status-pill.active {
  background: rgba(22, 163, 74, 0.12);
  color: #166534;
}

.mission-status-pill.building {
  background: rgba(234, 179, 8, 0.16);
  color: #854d0e;
}

.mission-status-pill.warming_up {
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
}

.mission-score-cluster strong {
  font-family: 'DM Mono', monospace;
  font-size: 32px;
  color: #0f172a;
}

.mission-chip-row,
.mission-deliverables {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mission-chip-row span,
.mission-deliverables span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.05);
  border: 1px solid rgba(15, 23, 42, 0.08);
  color: #334155;
  font-size: 12px;
  font-weight: 700;
}

.mission-subgrid,
.mission-lower-grid {
  display: grid;
  gap: 16px;
}

.mission-subgrid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.mission-subgrid strong,
.mission-panel-head span {
  display: inline-flex;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

.mission-lower-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.mission-panel {
  display: grid;
  gap: 12px;
  padding: 24px;
  border-radius: 28px;
}

.mission-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.mission-panel-head a {
  font-size: 13px;
  color: #475569;
}

.mission-line-item + .mission-line-item {
  padding-top: 10px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
}

.mission-empty {
  padding: 28px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px dashed rgba(15, 23, 42, 0.12);
  color: #475569;
  font-weight: 600;
}

.mission-empty.danger {
  color: #991b1b;
}

@media (max-width: 1280px) {
  .mission-metric-strip,
  .mission-grid,
  .mission-lower-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 980px) {
  .mission-hero,
  .mission-metric-strip,
  .mission-grid,
  .mission-lower-grid,
  .mission-subgrid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .mission-page {
    margin: -28px -16px;
    padding: 18px 16px 32px;
  }

  .mission-hero,
  .mission-lane-card,
  .mission-panel {
    padding: 22px;
  }

  .mission-lane-top {
    flex-direction: column;
  }

  .mission-score-cluster {
    justify-items: start;
  }
}
</style>
