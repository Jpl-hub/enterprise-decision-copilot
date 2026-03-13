<template>
  <section class="agent-workspace-panel meeting-workspace" :class="{ compact }">
    <div class="agent-workspace-head" :class="{ 'headless-workspace-head': !eyebrow && !title }">
      <div v-if="eyebrow || title">
        <p v-if="eyebrow" class="section-tag">{{ eyebrow }}</p>
        <h3 v-if="title">{{ title }}</h3>
      </div>
    </div>

    <div class="workspace-toolbar">
      <div class="task-mode-pill-group">
        <button
          v-for="item in taskModes"
          :key="item.value"
          type="button"
          class="task-mode-toggle"
          :class="{ active: activeTaskMode === item.value }"
          @click="selectTaskMode(item.value)"
        >
          {{ item.label }}
        </button>
      </div>
      <div class="workspace-toolbar-actions">
        <button class="button-ghost compact-action" @click="refreshHistory" :disabled="agentStore.loadingHistory">刷新历史</button>
        <button class="button-ghost compact-action" @click="resetThread">新建线程</button>
      </div>
    </div>

    <section class="meeting-stage-shell">
      <div class="meeting-stage-main">
        <div class="meeting-stage-topline">
          <div>
            <span class="meeting-stage-kicker">Decision Room</span>
            <strong>{{ stageTitle }}</strong>
          </div>
          <div class="meeting-stage-badges">
            <span class="meeting-badge accent">{{ activeTaskLabel }}</span>
            <span class="meeting-badge">{{ stageMeta }}</span>
          </div>
        </div>

        <div class="meeting-screen">
          <div class="meeting-screen-backdrop"></div>
          <div class="meeting-host-card">
            <div class="meeting-host-orb">
              <span>{{ focusInitial }}</span>
            </div>
            <div class="meeting-host-copy">
              <span class="meeting-host-label">主会场</span>
              <strong>{{ props.companyName || agentStore.focusCompanyName || '企业分析会场' }}</strong>
              <p>{{ stageSummary }}</p>
            </div>
          </div>

          <div class="meeting-pulse-strip">
            <article v-for="item in stageStats" :key="item.label" class="meeting-pulse-card">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </article>
          </div>
        </div>

        <div class="meeting-thinking-strip">
          <article v-for="item in compactThinkingSteps" :key="item.title" class="meeting-thinking-chip" :class="{ live: agentStore.loading && item.active }">
            <span>{{ item.title }}</span>
            <strong>{{ item.detail }}</strong>
          </article>
        </div>
      </div>

      <aside class="meeting-seat-rail">
        <div class="meeting-seat-rail-head">
          <span>参会席位</span>
          <strong>{{ visibleSeats.length }} 个</strong>
        </div>

        <div class="meeting-seat-grid">
          <article v-for="seat in visibleSeats" :key="seat.id" class="meeting-seat-card" :class="{ highlight: seat.highlight }">
            <div class="meeting-seat-avatar">{{ seat.avatar }}</div>
            <div class="meeting-seat-copy">
              <div class="meeting-seat-top">
                <strong>{{ seat.name }}</strong>
                <span>{{ seat.meta }}</span>
              </div>
              <p>{{ seat.summary }}</p>
            </div>
          </article>
        </div>

        <div class="meeting-seat-dock">
          <button v-for="item in starterPrompts" :key="item" class="meeting-dock-action" @click="applyPrompt(item)">
            {{ item }}
          </button>
        </div>
      </aside>
    </section>

    <div class="workspace-lower-grid">
      <section class="chat-room-card">
        <div class="chat-room-head">
          <div>
            <span class="chat-room-kicker">聊天室</span>
            <strong>{{ agentStore.threadTitle || '新线程' }}</strong>
          </div>
          <div class="chat-room-actions">
            <span class="chat-room-status">{{ agentStore.focusCompanyName || '未固定企业' }}</span>
            <button v-if="hasReasoningArtifacts" class="chat-room-toggle" @click="showReasoningDetails = !showReasoningDetails">
              {{ showReasoningDetails ? '收起推理' : '展开推理' }}
            </button>
          </div>
        </div>

        <div v-if="hasReasoningArtifacts" class="chat-reasoning-summary">
          <span v-for="item in reasoningSummaryChips" :key="item">{{ item }}</span>
        </div>

        <div v-if="showReasoningDetails && hasReasoningArtifacts" class="chat-reasoning-panel">
          <div class="chat-reasoning-column">
            <div class="chat-reasoning-head">
              <span>系统推演</span>
              <strong>{{ agentStore.latest?.trace?.length || 0 }} 步</strong>
            </div>
            <TracePanel :trace="agentStore.latest?.trace" />
          </div>
          <div class="chat-reasoning-column">
            <div class="chat-reasoning-head">
              <span>执行路线</span>
              <strong>{{ agentStore.latest?.plan?.length || 0 }} 步</strong>
            </div>
            <TracePanel :trace="agentStore.latest?.plan" />
          </div>
        </div>

        <div class="chat-scroll-shell">
          <AgentThreadPanel :messages="messagePreview" />
        </div>

        <div v-if="agentStore.error" class="error-banner">{{ agentStore.error }}</div>

        <div class="chat-input-row">
          <input v-model="draft" class="text-input hero-input" :placeholder="placeholder" @keydown.enter="submit" />
          <button class="button-primary hero-button" @click="submit" :disabled="agentStore.loading">发送</button>
        </div>
      </section>

      <aside class="workspace-right-rail">
        <section class="right-rail-card thread-history-card">
          <div class="right-rail-head">
            <div>
              <span>历史线程</span>
              <strong>最近会话</strong>
            </div>
            <RouterLink to="/threads">全部记录</RouterLink>
          </div>

          <div v-if="agentStore.loadingHistory" class="right-rail-empty">正在加载历史线程...</div>
          <div v-else-if="!agentStore.history.length" class="right-rail-empty">还没有历史线程，先开始一次分析。</div>
          <div v-else class="thread-history-list">
            <button
              v-for="item in historyItems"
              :key="item.thread_id"
              type="button"
              class="thread-history-item"
              :class="{ active: agentStore.threadId === item.thread_id }"
              @click="openThread(item.thread_id)"
            >
              <div class="thread-history-top">
                <strong>{{ item.title }}</strong>
                <span>{{ formatDate(item.updated_at) }}</span>
              </div>
              <p>{{ item.thread_summary || item.last_message || '本线程还没有摘要。' }}</p>
            </button>
          </div>
        </section>

        <section class="right-rail-card insight-card">
          <div class="right-rail-head">
            <div>
              <span>当前摘要</span>
              <strong>{{ insightTitle }}</strong>
            </div>
            <span class="right-rail-status">{{ insightStatus }}</span>
          </div>

          <div class="insight-hero">
            <p>{{ insightSummary }}</p>
          </div>

          <div class="insight-chip-grid">
            <article v-for="item in insightMetrics" :key="item.label" class="insight-chip-card">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </article>
          </div>
        </section>

        <section v-if="followUpQuestions.length" class="right-rail-card followup-card">
          <div class="right-rail-head">
            <div>
              <span>推荐追问</span>
              <strong>下一步怎么问</strong>
            </div>
          </div>

          <div class="followup-list">
            <button v-for="item in followUpQuestions" :key="item" class="followup-item" @click="applyPrompt(item)">
              {{ item }}
            </button>
          </div>
        </section>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink } from 'vue-router';

import AgentThreadPanel from './AgentThreadPanel.vue';
import TracePanel from './TracePanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';
import type { AgentBoardroomDebateRound, AgentBoardroomPanelist, AgentBoardroomSynthesis, AgentSQLPlaybook } from '../api/types';

const props = withDefaults(defineProps<{
  companyCode?: string | null;
  companyName?: string | null;
  seedQuestion?: string;
  title?: string;
  eyebrow?: string;
  compact?: boolean;
  placeholder?: string;
}>(), {
  seedQuestion: '',
  title: 'Agent 分析区',
  eyebrow: 'Agent',
  compact: false,
  placeholder: '输入你的问题',
});

const taskModes = [
  { value: 'company_diagnosis', label: '经营分析' },
  { value: 'company_risk_forecast', label: '风险判断' },
  { value: 'company_decision_brief', label: '决策建议' },
  { value: 'executive_boardroom', label: '协同会商' },
  { value: 'industry_trend', label: '行业趋势' },
  { value: 'data_quality', label: '数据治理' },
];

const loadingBlueprintMap: Record<string, Array<{ title: string; detail: string; active: boolean }>> = {
  company_diagnosis: [
    { title: '问题拆解', detail: '锁定问题范围', active: false },
    { title: '证据读取', detail: '汇总财报与研报', active: true },
    { title: '形成结论', detail: '输出经营判断', active: false },
  ],
  company_risk_forecast: [
    { title: '风险识别', detail: '提取风险因子', active: false },
    { title: '概率估计', detail: '计算高风险概率', active: true },
    { title: '给出动作', detail: '整理监测建议', active: false },
  ],
  executive_boardroom: [
    { title: '组局', detail: '拉起多席位会商', active: false },
    { title: '碰撞', detail: '收敛分歧点', active: true },
    { title: '落板', detail: '生成动作与红线', active: false },
  ],
  industry_trend: [
    { title: '抓主题', detail: '读取行业变化', active: false },
    { title: '做映射', detail: '定位公司影响', active: true },
    { title: '给建议', detail: '输出趋势判断', active: false },
  ],
  data_quality: [
    { title: '查覆盖', detail: '检查时效与缺口', active: false },
    { title: '扫异常', detail: '识别数据问题', active: true },
    { title: '排优先级', detail: '给出治理动作', active: false },
  ],
};

const taskModeLabels: Record<string, string> = {
  company_diagnosis: '经营分析',
  company_risk_forecast: '风险判断',
  company_decision_brief: '决策建议',
  executive_boardroom: '协同会商',
  industry_trend: '行业趋势',
  data_quality: '数据治理',
};

const previewSeats = [
  { id: 'finance', name: '财务席位', summary: '盯利润、现金流、资本开支。', meta: '数据核算', avatar: '财', highlight: false },
  { id: 'market', name: '市场席位', summary: '盯客户、渠道和增长空间。', meta: '增长判断', avatar: '市', highlight: true },
  { id: 'risk', name: '风险席位', summary: '盯坏情景、红线和触发点。', meta: '红线约束', avatar: '险', highlight: false },
  { id: 'avatar', name: '数字人席位', summary: '预留实时会话和数字人挂载位。', meta: '未来接入', avatar: '数', highlight: false },
];

const agentStore = useAgentThreadStore();
const draft = ref(props.seedQuestion);
const manualTaskMode = ref<string | null>(null);
const showReasoningDetails = ref(false);

const activeTaskMode = computed(() => manualTaskMode.value || agentStore.taskMode || 'company_diagnosis');
const activeTaskLabel = computed(() => taskModeLabels[activeTaskMode.value] || '企业分析');

const basePrompts = computed(() => {
  const companyName = props.companyName || '这家公司';
  const promptMap: Record<string, string[]> = {
    company_diagnosis: [
      `${companyName}当前最值得关注的经营问题是什么？`,
      `把${companyName}的经营状态拆成增长、盈利、现金流三层`,
      `${companyName}现在最需要管理层盯的变量是什么？`,
    ],
    company_risk_forecast: [
      `把${companyName}的风险拆成财务、经营、行业三层`,
      `${companyName}未来两年的高风险信号有哪些？`,
      `${companyName}当前最需要监测的风险指标是什么？`,
    ],
    company_decision_brief: [
      `给出${companyName}当前的经营判断和动作建议`,
      `${companyName}未来两年的主要机会与投入重点是什么？`,
      `如果管理层现在开会，${companyName}最该讨论什么？`,
    ],
    executive_boardroom: [
      `给${companyName}开一个管理层决策会议室`,
      `让财务、市场、风险和数据治理多个 agent 一起会诊${companyName}`,
      `把${companyName}做成一个适合答辩展示的多智能体协同场景`,
    ],
    industry_trend: [
      `${companyName}所在行业当前的趋势和主题变化是什么？`,
      `结合行业研报判断${companyName}面临的景气变化`,
      `这个赛道当前最重要的外部变量是什么？`,
    ],
    data_quality: [
      `${companyName}当前的数据覆盖和异常情况怎么样？`,
      `这家公司有哪些待处理的数据问题？`,
      `当前数据底座会不会影响${companyName}的判断可信度？`,
    ],
  };
  return promptMap[activeTaskMode.value] || promptMap.company_diagnosis;
});

const starterPrompts = computed(() => basePrompts.value.slice(0, props.compact ? 2 : 3));
const followUpQuestions = computed(() => agentStore.latest?.suggested_questions?.slice(0, props.compact ? 3 : 4) || []);
const routeCandidates = computed(() => agentStore.latest?.route_candidates?.slice(0, 2) || []);
const messagePreview = computed(() => props.compact ? agentStore.messages.slice(-4) : agentStore.messages);
const historyItems = computed(() => agentStore.history.slice(0, props.compact ? 5 : 6));

const boardroomPanelists = computed(() => (agentStore.latest?.panelists || []) as AgentBoardroomPanelist[]);
const boardroomRounds = computed(() => (agentStore.latest?.debate_rounds || []) as AgentBoardroomDebateRound[]);
const boardroomSynthesis = computed(() => (agentStore.latest?.synthesis || null) as AgentBoardroomSynthesis | null);
const boardroomPlaybook = computed(() => (agentStore.latest?.sql_playbook || null) as AgentSQLPlaybook | null);
const boardroomReady = computed(() => boardroomPanelists.value.length > 0 || boardroomRounds.value.length > 0 || !!boardroomSynthesis.value);

const focusInitial = computed(() => {
  const name = props.companyName || agentStore.focusCompanyName || '企';
  return name.slice(0, 1);
});

const stageTitle = computed(() => {
  if (boardroomReady.value) return boardroomSynthesis.value?.primary_call || '多席位协同会商中';
  return '把页面做成会议，不是做成一篇长文档';
});

const stageMeta = computed(() => {
  if (boardroomReady.value) return `可信度 ${boardroomSynthesis.value?.confidence?.toFixed(2) || '0.00'}`;
  return '腾讯会议式布局';
});

const stageSummary = computed(() => {
  if (boardroomReady.value) {
    return boardroomSynthesis.value?.consensus_summary || '多个席位正在围绕同一企业汇总判断。';
  }
  return '主舞台负责展示当前会商主题、主讲席位和关键动作，后面接数字人或 WebSocket 实时会话时直接扩展这里。';
});

const stageStats = computed(() => {
  if (boardroomReady.value) {
    return [
      { label: '与会角色', value: `${boardroomPanelists.value.length} 个` },
      { label: '辩论轮次', value: `${boardroomRounds.value.length} 轮` },
      { label: '动作任务', value: `${boardroomPlaybook.value?.missions?.length || 0} 项` },
    ];
  }
  return [
    { label: '会场模式', value: activeTaskLabel.value },
    { label: '历史线程', value: `${agentStore.history.length} 条` },
    { label: '问题入口', value: '聊天室' },
  ];
});

const visibleSeats = computed(() => {
  if (!boardroomReady.value) return previewSeats;
  return boardroomPanelists.value.slice(0, 4).map((item, index) => ({
    id: item.agent_id,
    name: item.role_label,
    summary: item.stance,
    meta: `${item.confidence.toFixed(2)}${item.sql_focus ? ` · ${item.sql_focus}` : ''}`,
    avatar: item.role_label.slice(0, 1),
    highlight: index === 0,
  }));
});

const compactThinkingSteps = computed(() => {
  if (agentStore.latest?.trace?.length) {
    return agentStore.latest.trace.slice(0, 3).map((item, index) => ({
      title: item.step,
      detail: item.detail,
      active: index === 1,
    }));
  }
  return loadingBlueprintMap[activeTaskMode.value] || loadingBlueprintMap.company_diagnosis;
});

const reasoningSummaryChips = computed(() => {
  const chips: string[] = [];
  if (agentStore.latest?.stage_label) chips.push(agentStore.latest.stage_label);
  if (agentStore.latest?.deliverables?.length) chips.push(...agentStore.latest.deliverables.slice(0, 2));
  if (routeCandidates.value.length) chips.push(`候选路径 ${routeCandidates.value.length} 条`);
  if (agentStore.latest?.execution_digest?.evidence_count != null) chips.push(`证据 ${agentStore.latest.execution_digest.evidence_count} 条`);
  return chips.slice(0, 5);
});

const hasReasoningArtifacts = computed(() => Boolean(
  agentStore.latest?.trace?.length ||
  agentStore.latest?.plan?.length ||
  routeCandidates.value.length ||
  agentStore.latest?.execution_digest,
));

const insightTitle = computed(() => agentStore.latest?.title || agentStore.threadTitle || '等待本轮摘要');
const insightStatus = computed(() => agentStore.latest?.stage_label || activeTaskLabel.value);
const insightSummary = computed(() => {
  if (agentStore.latest?.summary) return agentStore.latest.summary;
  if (agentStore.threadSummary) return agentStore.threadSummary;
  return '右侧只保留必要的摘要、指标和推荐追问，不再堆满说明文字。';
});

const insightMetrics = computed(() => {
  const cards: Array<{ label: string; value: string }> = [];
  if (agentStore.latest?.execution_digest) {
    cards.push({ label: '证据', value: `${agentStore.latest.execution_digest.evidence_count} 条` });
    cards.push({ label: '步骤', value: `${agentStore.latest.execution_digest.plan_step_count} 步` });
  } else if (agentStore.threadMemory?.key_signals?.length) {
    cards.push({ label: '关键点', value: `${agentStore.threadMemory.key_signals.length} 条` });
  }
  if (boardroomReady.value) {
    cards.push({ label: '席位', value: `${boardroomPanelists.value.length} 个` });
  }
  if (agentStore.history.length) {
    cards.push({ label: '历史', value: `${agentStore.history.length} 条` });
  }
  return cards.slice(0, 4);
});

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function resetThread() {
  manualTaskMode.value = null;
  agentStore.resetThread(props.companyCode, props.companyName);
  draft.value = props.seedQuestion || basePrompts.value[0];
  showReasoningDetails.value = false;
}

function selectTaskMode(taskMode: string) {
  manualTaskMode.value = taskMode;
  agentStore.setTaskMode(taskMode);
  draft.value = basePrompts.value[0];
}

function applyPrompt(text: string) {
  draft.value = text;
  void submit();
}

async function refreshHistory() {
  await agentStore.loadHistory();
}

async function openThread(threadId: string) {
  showReasoningDetails.value = false;
  manualTaskMode.value = null;
  await agentStore.openThread(threadId);
}

async function submit() {
  const question = draft.value.trim();
  if (!question) return;
  showReasoningDetails.value = false;
  await agentStore.ask(question, {
    companyCode: props.companyCode,
    companyName: props.companyName,
    taskMode: manualTaskMode.value ?? undefined,
  });
  draft.value = '';
}

watch(() => props.seedQuestion, (value) => {
  if (value) draft.value = value;
}, { immediate: true });

watch(() => [props.companyCode, props.companyName], ([companyCode, companyName]) => {
  manualTaskMode.value = null;
  if (companyCode || companyName) agentStore.setFocus(companyCode, companyName);
}, { immediate: true });

onMounted(async () => {
  if (!agentStore.history.length && !agentStore.loadingHistory) {
    await refreshHistory();
  }
});
</script>

<style scoped>
.meeting-workspace,
.workspace-toolbar,
.workspace-toolbar-actions,
.meeting-stage-shell,
.meeting-stage-main,
.meeting-seat-rail,
.meeting-seat-grid,
.meeting-seat-dock,
.meeting-stage-badges,
.meeting-pulse-strip,
.meeting-thinking-strip,
.workspace-lower-grid,
.workspace-right-rail,
.thread-history-list,
.followup-list,
.insight-chip-grid,
.chat-reasoning-panel,
.chat-reasoning-column {
  display: grid;
  gap: 16px;
}

.meeting-workspace {
  gap: 18px;
}

.workspace-toolbar {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.workspace-toolbar-actions {
  grid-auto-flow: column;
}

.meeting-stage-shell,
.chat-room-card,
.right-rail-card {
  border-radius: 28px;
  overflow: hidden;
}

.meeting-stage-shell {
  grid-template-columns: minmax(0, 1.45fr) minmax(300px, 0.62fr);
  padding: 18px;
  background:
    radial-gradient(circle at top left, rgba(72, 255, 183, 0.18), transparent 22%),
    radial-gradient(circle at bottom right, rgba(255, 164, 96, 0.12), transparent 24%),
    linear-gradient(135deg, #0b1627, #162c4a 54%, #213f66);
  border: 1px solid rgba(159, 198, 235, 0.18);
  box-shadow: 0 26px 80px rgba(7, 14, 26, 0.28);
}

.meeting-stage-topline,
.meeting-seat-rail-head,
.chat-room-head,
.right-rail-head,
.thread-history-top,
.meeting-seat-top,
.chat-reasoning-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.meeting-stage-kicker,
.chat-room-kicker,
.right-rail-head span:first-child,
.meeting-seat-rail-head span {
  display: inline-flex;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 700;
}

.meeting-stage-kicker,
.meeting-seat-rail-head span {
  color: rgba(222, 234, 248, 0.72);
}

.chat-room-kicker,
.right-rail-head span:first-child {
  color: #687a92;
}

.meeting-stage-topline strong,
.chat-room-head strong,
.right-rail-head strong {
  display: block;
  font-size: 24px;
  line-height: 1.12;
}

.meeting-stage-topline strong {
  color: #f3f8ff;
}

.meeting-stage-badges {
  grid-auto-flow: column;
  align-items: center;
}

.meeting-badge {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 12px;
  color: #dce8f5;
}

.meeting-badge.accent {
  background: rgba(78, 142, 255, 0.18);
  color: #fff;
}

.meeting-screen {
  position: relative;
  min-height: 360px;
  padding: 28px;
  border-radius: 26px;
  background: linear-gradient(180deg, rgba(245, 249, 255, 0.04), rgba(9, 21, 39, 0.18));
  border: 1px solid rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.meeting-screen-backdrop {
  position: absolute;
  inset: -20%;
  background:
    radial-gradient(circle at center, rgba(83, 198, 255, 0.28), transparent 24%),
    radial-gradient(circle at 70% 28%, rgba(76, 255, 160, 0.18), transparent 18%),
    radial-gradient(circle at 32% 74%, rgba(255, 176, 109, 0.16), transparent 16%);
  filter: blur(18px);
}

.meeting-host-card,
.meeting-pulse-strip,
.meeting-thinking-strip {
  position: relative;
  z-index: 1;
}

.meeting-host-card {
  display: grid;
  place-items: center;
  gap: 20px;
  padding-top: 10px;
}

.meeting-host-orb {
  display: grid;
  place-items: center;
  width: 168px;
  height: 168px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 30%, #8be3ff, #2d73ff 52%, #102349 78%);
  border: 8px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 0 0 16px rgba(115, 181, 255, 0.08), 0 20px 44px rgba(0, 0, 0, 0.34);
  color: #fff;
  font-size: 54px;
  font-weight: 800;
}

.meeting-host-copy {
  max-width: 620px;
  text-align: center;
}

.meeting-host-label {
  display: inline-flex;
  margin-bottom: 10px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: #d9e7f7;
  font-size: 12px;
}

.meeting-host-copy strong {
  display: block;
  font-size: 34px;
  line-height: 1.12;
  color: #f4f8ff;
}

.meeting-host-copy p {
  margin: 12px 0 0;
  color: rgba(226, 236, 247, 0.84);
  line-height: 1.7;
}

.meeting-pulse-strip {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 28px;
}

.meeting-pulse-card,
.meeting-thinking-chip,
.meeting-seat-card,
.meeting-dock-action,
.thread-history-item,
.insight-chip-card,
.followup-item,
.chat-reasoning-panel,
.chat-reasoning-column {
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.meeting-pulse-card {
  padding: 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
}

.meeting-pulse-card span {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: rgba(218, 230, 245, 0.72);
}

.meeting-pulse-card strong {
  font-size: 22px;
  color: #fff;
}

.meeting-thinking-strip {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.meeting-thinking-chip {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(248, 251, 255, 0.06);
}

.meeting-thinking-chip.live {
  background: rgba(78, 142, 255, 0.2);
  box-shadow: inset 0 0 0 1px rgba(146, 195, 255, 0.32);
}

.meeting-thinking-chip span {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: rgba(214, 228, 242, 0.68);
}

.meeting-thinking-chip strong {
  color: #f4f8ff;
  font-size: 15px;
  line-height: 1.45;
}

.meeting-seat-rail {
  align-content: start;
  padding: 18px;
  border-radius: 24px;
  background: rgba(6, 13, 24, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.meeting-seat-rail-head strong {
  color: #fff;
}

.meeting-seat-grid {
  max-height: 408px;
  overflow: auto;
}

.meeting-seat-card {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr);
  gap: 14px;
  padding: 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
}

.meeting-seat-card.highlight {
  background: linear-gradient(135deg, rgba(61, 109, 224, 0.22), rgba(63, 193, 167, 0.14));
}

.meeting-seat-avatar {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 22px;
  font-weight: 700;
}

.meeting-seat-copy p {
  margin: 8px 0 0;
  color: rgba(227, 236, 246, 0.82);
  line-height: 1.55;
}

.meeting-seat-top strong {
  color: #f4f8ff;
}

.meeting-seat-top span {
  font-size: 12px;
  color: rgba(214, 228, 242, 0.68);
}

.meeting-seat-dock {
  grid-template-columns: 1fr;
}

.meeting-dock-action {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.06);
  color: #f4f8ff;
  text-align: left;
  cursor: pointer;
}

.workspace-lower-grid {
  grid-template-columns: minmax(0, 1.25fr) minmax(310px, 0.75fr);
  align-items: start;
}

.chat-room-card,
.right-rail-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 249, 252, 0.98));
  border: 1px solid rgba(10, 31, 68, 0.08);
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.07);
}

.chat-room-card {
  padding: 18px;
}

.chat-room-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-room-status {
  font-size: 12px;
  color: var(--text-secondary);
}

.chat-room-toggle {
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(10, 31, 68, 0.08);
  background: #f3f7fb;
  color: var(--text-primary);
  cursor: pointer;
}

.chat-reasoning-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chat-reasoning-summary span {
  padding: 8px 12px;
  border-radius: 999px;
  background: #edf4fb;
  color: #32557d;
  font-size: 12px;
  font-weight: 600;
}

.chat-reasoning-panel {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  padding: 14px;
  border-radius: 22px;
  background: #f6f9fc;
}

.chat-reasoning-column {
  padding: 14px;
  border-radius: 18px;
  background: #fff;
}

.chat-reasoning-head span {
  font-size: 12px;
  color: var(--text-secondary);
}

.chat-scroll-shell {
  height: 420px;
  overflow: auto;
  padding: 12px 6px 12px 0;
  border-radius: 22px;
  border: 1px solid rgba(10, 31, 68, 0.08);
  background:
    radial-gradient(circle at top right, rgba(37, 89, 160, 0.08), transparent 20%),
    linear-gradient(180deg, #f9fbfd, #f3f6fa);
}

.chat-scroll-shell :deep(.thread-timeline) {
  padding: 16px;
}

.chat-input-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 108px;
  gap: 12px;
  align-items: center;
}

.workspace-right-rail {
  position: sticky;
  top: 16px;
}

.right-rail-card {
  padding: 18px;
}

.right-rail-head strong {
  font-size: 20px;
}

.right-rail-head a,
.right-rail-status {
  font-size: 12px;
  color: var(--text-secondary);
  text-decoration: none;
}

.thread-history-list {
  max-height: 320px;
  overflow: auto;
}

.thread-history-item {
  padding: 14px;
  border-radius: 18px;
  background: #f8fbfd;
  text-align: left;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
}

.thread-history-item:hover,
.thread-history-item.active,
.followup-item:hover {
  transform: translateY(-1px);
  border-color: rgba(31, 78, 146, 0.2);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}

.thread-history-top span {
  font-size: 12px;
  color: var(--text-secondary);
}

.thread-history-item p,
.insight-hero p,
.right-rail-empty {
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.insight-hero {
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, #f4f8fc, #edf3f9);
}

.insight-chip-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.insight-chip-card {
  padding: 14px;
  border-radius: 16px;
  background: #f8fbfd;
}

.insight-chip-card span {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.insight-chip-card strong {
  color: var(--text-primary);
}

.followup-list {
  grid-template-columns: 1fr;
}

.followup-item {
  padding: 14px;
  border-radius: 16px;
  background: #f8fbfd;
  text-align: left;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
}

@media (max-width: 1280px) {
  .meeting-stage-shell,
  .workspace-lower-grid,
  .chat-reasoning-panel {
    grid-template-columns: 1fr;
  }

  .workspace-right-rail {
    position: static;
  }
}

@media (max-width: 760px) {
  .workspace-toolbar {
    grid-template-columns: 1fr;
  }

  .workspace-toolbar-actions {
    grid-auto-flow: row;
  }

  .meeting-stage-topline,
  .meeting-seat-rail-head,
  .chat-room-head,
  .right-rail-head,
  .thread-history-top,
  .meeting-seat-top,
  .chat-reasoning-head {
    flex-direction: column;
    align-items: start;
  }

  .meeting-pulse-strip,
  .meeting-thinking-strip,
  .insight-chip-grid,
  .chat-input-row {
    grid-template-columns: 1fr;
  }

  .chat-scroll-shell,
  .thread-history-list,
  .meeting-seat-grid {
    max-height: none;
    height: auto;
  }
}
</style>
