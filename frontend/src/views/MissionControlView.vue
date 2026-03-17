<template>
  <div class="mission-page">
    <div class="mission-shell">
      <header class="mission-hero">
        <div class="mission-hero-copy">
          <span class="mission-kicker">业务总览</span>
          <h1>查看当前系统能做什么、数据够不够新、结果能不能直接用</h1>
          <p>
            这里不讲产品外叙事，只讲用户真正关心的三件事：系统当前有哪些分析能力、底层数据是否可信、结果是否适合直接继续使用。
          </p>
          <div class="mission-audience-row">
            <span>当前可用能力</span>
            <span>数据可信状态</span>
            <span>结果交付能力</span>
          </div>
        </div>
        <div class="mission-hero-side" v-if="payload">
          <div class="mission-gate-badge" :class="payload.release_gate.gate_status">
            <span>当前可用性</span>
            <strong>{{ gateLabel }}</strong>
          </div>
          <p>{{ payload.release_gate.release_note }}</p>
        </div>
      </header>

      <section class="mission-top-strip">
        <article class="mission-panel mission-mini-panel">
          <div class="mission-panel-head">
            <span>你现在能用什么</span>
            <strong>围绕企业问答、报告、风险和导出使用系统</strong>
          </div>
          <div class="mission-mini-tags">
            <span>企业问答</span>
            <span>企业对比</span>
            <span>报告导出</span>
          </div>
        </article>

        <article class="mission-panel mission-mini-panel">
          <div class="mission-panel-head">
            <span>当前最重要</span>
            <strong>先看可用能力，再看证据，再决定要不要继续深入</strong>
          </div>
          <div class="mission-mini-tags">
            <span>能力状态</span>
            <span>数据新鲜度</span>
            <span>结果可信度</span>
          </div>
        </article>
      </section>

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

      <section v-if="payload" class="mission-visual-grid">
        <article class="mission-panel">
          <div class="mission-panel-head">
            <span>能力状态分布</span>
            <div class="mission-filter-row">
              <button
                v-for="lane in payload.mission_lanes"
                :key="lane.lane_id"
                class="mission-filter-chip"
                :class="{ active: selectedLaneId === lane.lane_id }"
                @click="selectedLaneId = lane.lane_id"
              >
                {{ lane.name }}
              </button>
            </div>
          </div>
          <EChartPanel :option="laneChartOption" height="320px" @chart-click="handleLaneChartClick" />
        </article>

        <article class="mission-panel mission-focus-panel" v-if="selectedLane">
          <div class="mission-panel-head">
            <span>当前焦点能力</span>
            <strong>{{ selectedLane.name }}</strong>
          </div>
          <p class="mission-focus-copy">{{ selectedLane.summary }}</p>
          <div class="mission-focus-readiness">
            <span class="mission-status-pill" :class="selectedLane.status">{{ statusLabel(selectedLane.status) }}</span>
            <strong>{{ (selectedLane.readiness_score * 100).toFixed(0) }}</strong>
          </div>
          <div class="mission-focus-box">
            <span>当前状态</span>
            <p>{{ selectedLane.current_focus }}</p>
          </div>
          <div class="mission-focus-box">
            <span>推荐继续使用</span>
            <p v-for="item in selectedLane.next_actions" :key="item">{{ item }}</p>
          </div>
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
          <div class="mission-progress-track">
            <div class="mission-progress-bar" :style="{ width: `${Math.max(8, Math.round(lane.readiness_score * 100))}%` }"></div>
          </div>
          <div class="mission-focus-box compact">
            <span>当前状态</span>
            <p>{{ lane.current_focus }}</p>
          </div>

          <div class="mission-chip-row" v-if="lane.linked_engines.length">
            <span v-for="item in lane.linked_engines" :key="item">{{ item }}</span>
          </div>

          <div class="mission-subgrid">
            <div>
              <strong>当前限制</strong>
              <p v-for="item in laneBlockers(lane)" :key="item">{{ item }}</p>
            </div>
            <div>
              <strong>继续完善</strong>
              <p v-for="item in laneNextActions(lane)" :key="item">{{ item }}</p>
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
            <span>常用路径</span>
            <RouterLink to="/">开始分析</RouterLink>
          </div>
          <p v-for="item in payload.showcase_flows" :key="item" class="mission-line-item">{{ item }}</p>
        </article>

        <article class="mission-panel">
          <div class="mission-panel-head">
            <span>系统摘要</span>
            <RouterLink to="/workbench">进入企业分析</RouterLink>
          </div>
          <p v-for="item in payload.control_tower_brief" :key="item" class="mission-line-item">{{ item }}</p>
        </article>
      </section>

      <div v-if="loading" class="mission-empty">正在加载业务总览...</div>
      <div v-else-if="error" class="mission-empty danger">{{ error }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink } from 'vue-router';
import { api } from '../api/client';
import type { AIMissionControlResponse, AIMissionLane } from '../api/types';
import EChartPanel from '../components/EChartPanel.vue';

const payload = ref<AIMissionControlResponse | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const selectedLaneId = ref('');

function statusLabel(status: string) {
  if (status === 'active') return '运行中';
  if (status === 'building') return '建设中';
  return '预热中';
}

const selectedLane = computed(() => payload.value?.mission_lanes.find((item) => item.lane_id === selectedLaneId.value) || payload.value?.mission_lanes?.[0] || null);
const gateLabel = computed(() => payload.value?.release_gate.gate_status === 'open' ? '可直接使用' : '建议先复查');

const laneChartOption = computed(() => {
  const lanes = payload.value?.mission_lanes || [];
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 24, right: 24, top: 24, bottom: 70, containLabel: true },
    xAxis: {
      type: 'category',
      data: lanes.map((item) => item.name),
      axisLabel: { color: '#64748b', interval: 0, rotate: 18 },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#e2e8f0' } },
    },
    series: [
      {
        type: 'bar',
        data: lanes.map((item) => Number((item.readiness_score * 100).toFixed(0))),
        itemStyle: {
          color: (params: { dataIndex: number }) => {
            const lane = lanes[params.dataIndex];
            if (!lane) return '#173f78';
            if (lane.status === 'active') return '#166534';
            if (lane.status === 'building') return '#d97706';
            return '#2563eb';
          },
          borderRadius: [10, 10, 0, 0],
        },
      },
    ],
  };
});

function handleLaneChartClick(params: Record<string, unknown>) {
  const laneName = String(params.name || '');
  const lane = payload.value?.mission_lanes.find((item) => item.name === laneName);
  if (lane) {
    selectedLaneId.value = lane.lane_id;
  }
}

function laneBlockers(lane: AIMissionLane) {
  return lane.blockers.slice(0, 2).map(formatMissionNote);
}

function laneNextActions(lane: AIMissionLane) {
  return lane.next_actions.slice(0, 2).map(formatMissionNote);
}

function formatMissionNote(value: string) {
  const text = String(value || '').trim();
  if (!text) return text;
  if (text.startsWith('{') && text.includes("'title'")) {
    const titleMatch = text.match(/'title':\s*'([^']+)'/);
    const detailMatch = text.match(/'detail':\s*'([^']+)'/);
    if (titleMatch?.[1] && detailMatch?.[1]) {
      return `${titleMatch[1]}：${detailMatch[1]}`;
    }
    if (titleMatch?.[1]) {
      return titleMatch[1];
    }
  }
  return text;
}

onMounted(async () => {
  loading.value = true;
  error.value = null;
  try {
    payload.value = await api.getAIMissionControl();
    selectedLaneId.value = payload.value.mission_lanes[0]?.lane_id || '';
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载业务总览失败';
  } finally {
    loading.value = false;
  }
});

watch(payload, (value) => {
  if (value?.mission_lanes?.length && !value.mission_lanes.some((item) => item.lane_id === selectedLaneId.value)) {
    selectedLaneId.value = value.mission_lanes[0].lane_id;
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
  gap: 18px;
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
  gap: 20px;
  padding: 26px 30px;
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
  margin: 14px 0 10px;
  font-family: 'Syne', 'DM Sans', sans-serif;
  font-size: clamp(34px, 4vw, 58px);
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

.mission-audience-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.mission-audience-row span {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.05);
  border: 1px solid rgba(15, 23, 42, 0.08);
  color: #334155;
  font-size: 12px;
  font-weight: 700;
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

.mission-top-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.mission-metric-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
}

.mission-visual-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 18px;
}

.mission-filter-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.mission-filter-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: #ffffff;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mission-filter-chip:hover {
  border-color: #0f172a;
  color: #0f172a;
}

.mission-filter-chip.active {
  background: #0f172a;
  color: #ffffff;
  border-color: #0f172a;
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

.mission-mini-panel {
  gap: 14px;
}

.mission-mini-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mission-mini-tags span {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.05);
  border: 1px solid rgba(15, 23, 42, 0.08);
  color: #334155;
  font-size: 12px;
  font-weight: 700;
}

.mission-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.mission-lane-card {
  display: grid;
  gap: 14px;
  padding: 22px;
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

.mission-progress-track {
  height: 10px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.18);
  overflow: hidden;
}

.mission-progress-bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #0f172a, #2563eb);
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

.mission-focus-panel {
  align-content: start;
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

.mission-focus-copy {
  margin: 0;
  font-size: 15px;
  line-height: 1.8;
  color: #475569;
}

.mission-focus-readiness {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.04);
}

.mission-focus-readiness strong {
  font-family: 'DM Mono', monospace;
  font-size: 28px;
  color: #0f172a;
}

.mission-focus-box {
  display: grid;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.mission-focus-box.compact {
  padding: 12px 14px;
}

.mission-focus-box span {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

.mission-focus-box p {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: #334155;
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
  .mission-top-strip,
  .mission-metric-strip,
  .mission-grid,
  .mission-lower-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 980px) {
  .mission-hero,
  .mission-top-strip,
  .mission-visual-grid,
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
