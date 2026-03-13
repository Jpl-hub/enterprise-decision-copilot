<template>
  <section class="qa-console">
    <div class="qa-console-head">
      <div>
        <span class="qa-console-kicker">Question Console</span>
        <strong>{{ props.companyName || agentStore.focusCompanyName || '企业问答' }}</strong>
      </div>
      <div class="qa-console-actions">
        <label class="qa-mode-select">
          <span>模式</span>
          <select :value="activeTaskMode" @change="selectTaskMode(($event.target as HTMLSelectElement).value)">
            <option v-for="item in taskModes" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
        </label>
        <button class="button-ghost compact-action" @click="toggleHistory">
          {{ showHistory ? '收起历史' : '历史线程' }}
        </button>
        <button class="button-ghost compact-action" @click="resetThread">新建线程</button>
      </div>
    </div>

    <div class="qa-summary-strip">
      <span class="qa-summary-title">{{ summaryTitle }}</span>
      <span v-for="item in summaryChips" :key="item" class="qa-summary-chip">{{ item }}</span>
    </div>

    <div v-if="showHistory" class="qa-history-drawer">
      <div class="qa-history-head">
        <strong>最近线程</strong>
        <button class="qa-link-button" @click="refreshHistory" :disabled="agentStore.loadingHistory">刷新</button>
      </div>

      <div v-if="agentStore.loadingHistory" class="qa-empty-state">正在加载历史线程...</div>
      <div v-else-if="!agentStore.history.length" class="qa-empty-state">还没有历史线程。</div>
      <div v-else class="qa-history-grid">
        <button
          v-for="item in historyItems"
          :key="item.thread_id"
          type="button"
          class="qa-history-card"
          :class="{ active: agentStore.threadId === item.thread_id }"
          @click="openThread(item.thread_id)"
        >
          <div class="qa-history-top">
            <strong>{{ item.title }}</strong>
            <span>{{ formatDate(item.updated_at) }}</span>
          </div>
          <p>{{ item.thread_summary || item.last_message || '本线程还没有摘要。' }}</p>
        </button>
      </div>
    </div>

    <div class="qa-reasoning-bar">
      <div class="qa-reasoning-head">
        <div>
          <span>推理状态</span>
          <strong>{{ agentStore.loading ? '系统正在整理回答' : '先状态，后答案' }}</strong>
        </div>
        <button v-if="hasReasoningArtifacts" class="qa-link-button" @click="showReasoning = !showReasoning">
          {{ showReasoning ? '收起过程' : '展开过程' }}
        </button>
      </div>

      <div class="qa-status-row">
        <article v-for="item in reasoningPreview" :key="item.title" class="qa-status-card" :class="{ live: agentStore.loading && item.live }">
          <span>{{ item.title }}</span>
          <strong>{{ item.detail }}</strong>
        </article>
      </div>

      <div v-if="showReasoning && hasReasoningArtifacts" class="qa-reasoning-detail">
        <div class="qa-trace-column">
          <div class="qa-trace-head">
            <span>系统推演</span>
            <strong>{{ agentStore.latest?.trace?.length || 0 }} 步</strong>
          </div>
          <TracePanel :trace="agentStore.latest?.trace" />
        </div>
        <div class="qa-trace-column">
          <div class="qa-trace-head">
            <span>执行路线</span>
            <strong>{{ agentStore.latest?.plan?.length || 0 }} 步</strong>
          </div>
          <TracePanel :trace="agentStore.latest?.plan" />
        </div>
      </div>
    </div>

    <section class="qa-chat-panel">
      <div class="qa-chat-head">
        <div>
          <span>当前线程</span>
          <strong>{{ agentStore.threadTitle || '新线程' }}</strong>
        </div>
        <div class="qa-chat-meta">
          <span>{{ activeTaskLabel }}</span>
          <span>{{ agentStore.focusCompanyName || '未固定企业' }}</span>
        </div>
      </div>

      <div class="qa-chat-scroll">
        <AgentThreadPanel :messages="messagePreview" />
      </div>

      <div v-if="agentStore.error" class="error-banner">{{ agentStore.error }}</div>

      <div class="qa-input-row">
        <input v-model="draft" class="text-input hero-input" :placeholder="placeholder" @keydown.enter="submit" />
        <button class="button-primary hero-button" @click="submit" :disabled="agentStore.loading">发送</button>
      </div>

      <div v-if="followUpQuestions.length" class="qa-followup-row">
        <button v-for="item in followUpQuestions" :key="item" class="qa-followup-chip" @click="applyPrompt(item)">
          {{ item }}
        </button>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';

import AgentThreadPanel from './AgentThreadPanel.vue';
import TracePanel from './TracePanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';

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
  { value: 'industry_trend', label: '行业趋势' },
  { value: 'data_quality', label: '数据治理' },
];

const taskModeLabels: Record<string, string> = {
  company_diagnosis: '经营分析',
  company_risk_forecast: '风险判断',
  company_decision_brief: '决策建议',
  industry_trend: '行业趋势',
  data_quality: '数据治理',
};

const loadingPreviewMap: Record<string, Array<{ title: string; detail: string; live: boolean }>> = {
  company_diagnosis: [
    { title: '问题拆解', detail: '确认范围', live: false },
    { title: '证据读取', detail: '汇总财报与研报', live: true },
    { title: '生成结论', detail: '给出经营判断', live: false },
  ],
  company_risk_forecast: [
    { title: '提取风险', detail: '识别风险因子', live: false },
    { title: '计算概率', detail: '生成风险等级', live: true },
    { title: '整理动作', detail: '输出监测建议', live: false },
  ],
  company_decision_brief: [
    { title: '问题聚焦', detail: '锁定管理问题', live: false },
    { title: '拉齐证据', detail: '汇总判断依据', live: true },
    { title: '形成建议', detail: '生成动作结论', live: false },
  ],
  industry_trend: [
    { title: '抓主题', detail: '提取行业变化', live: false },
    { title: '做映射', detail: '判断公司影响', live: true },
    { title: '给建议', detail: '输出行业判断', live: false },
  ],
  data_quality: [
    { title: '查覆盖', detail: '检查时效与缺口', live: false },
    { title: '扫异常', detail: '识别数据问题', live: true },
    { title: '排优先级', detail: '整理治理建议', live: false },
  ],
};

const agentStore = useAgentThreadStore();
const draft = ref(props.seedQuestion);
const manualTaskMode = ref<string | null>(null);
const showReasoning = ref(false);
const showHistory = ref(false);

const activeTaskMode = computed(() => manualTaskMode.value || agentStore.taskMode || 'company_diagnosis');
const activeTaskLabel = computed(() => taskModeLabels[activeTaskMode.value] || '企业分析');
const messagePreview = computed(() => props.compact ? agentStore.messages.slice(-4) : agentStore.messages);
const followUpQuestions = computed(() => agentStore.latest?.suggested_questions?.slice(0, props.compact ? 3 : 4) || []);
const historyItems = computed(() => agentStore.history.slice(0, props.compact ? 5 : 8));

const reasoningPreview = computed(() => {
  if (agentStore.latest?.trace?.length) {
    return agentStore.latest.trace.slice(0, 3).map((item, index) => ({
      title: item.step,
      detail: item.detail,
      live: index === 1,
    }));
  }
  return loadingPreviewMap[activeTaskMode.value] || loadingPreviewMap.company_diagnosis;
});

const hasReasoningArtifacts = computed(() => Boolean(agentStore.latest?.trace?.length || agentStore.latest?.plan?.length));
const summaryTitle = computed(() => agentStore.latest?.title || agentStore.threadTitle || '等待本轮回答');
const summaryChips = computed(() => {
  const chips = [
    activeTaskLabel.value,
    agentStore.focusCompanyName || '未固定企业',
  ];
  if (agentStore.latest?.execution_digest?.evidence_count != null) {
    chips.push(`证据 ${agentStore.latest.execution_digest.evidence_count} 条`);
  }
  if (followUpQuestions.value.length) {
    chips.push(`追问 ${followUpQuestions.value.length} 条`);
  }
  return chips.filter(Boolean).slice(0, 5);
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
  showReasoning.value = false;
  agentStore.resetThread(props.companyCode, props.companyName);
  draft.value = props.seedQuestion || '';
}

function selectTaskMode(taskMode: string) {
  manualTaskMode.value = taskMode;
  agentStore.setTaskMode(taskMode);
}

function toggleHistory() {
  showHistory.value = !showHistory.value;
}

function applyPrompt(text: string) {
  draft.value = text;
  void submit();
}

async function refreshHistory() {
  await agentStore.loadHistory();
}

async function openThread(threadId: string) {
  showReasoning.value = false;
  await agentStore.openThread(threadId);
}

async function submit() {
  const question = draft.value.trim();
  if (!question) return;
  showReasoning.value = false;
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
.qa-console,
.qa-console-actions,
.qa-history-grid,
.qa-status-row,
.qa-reasoning-detail,
.qa-followup-row {
  display: grid;
  gap: 14px;
}

.qa-console {
  padding: 18px;
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 249, 252, 0.98));
  border: 1px solid rgba(10, 31, 68, 0.08);
  box-shadow: 0 22px 64px rgba(15, 23, 42, 0.07);
}

.qa-console-head,
.qa-history-head,
.qa-reasoning-head,
.qa-chat-head,
.qa-history-top,
.qa-trace-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.qa-console-kicker,
.qa-reasoning-head span,
.qa-chat-head span {
  display: inline-flex;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 700;
  color: #6a7b90;
}

.qa-console-head strong,
.qa-chat-head strong {
  display: block;
  line-height: 1.12;
}

.qa-console-head strong {
  font-size: 28px;
}

.qa-console-actions {
  grid-auto-flow: column;
  align-items: center;
}

.qa-mode-select {
  display: grid;
  gap: 6px;
  min-width: 148px;
}

.qa-mode-select span {
  font-size: 12px;
  color: var(--text-secondary);
}

.qa-mode-select select {
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(10, 31, 68, 0.1);
  background: #fff;
  color: var(--text-primary);
}

.qa-summary-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  padding: 12px 0 4px;
}

.qa-summary-title {
  font-weight: 700;
  color: var(--text-primary);
  margin-right: 6px;
}

.qa-summary-chip,
.qa-chat-meta span {
  padding: 8px 12px;
  border-radius: 999px;
  background: #edf3f9;
  color: #35577f;
  font-size: 12px;
}

.qa-history-drawer,
.qa-reasoning-bar,
.qa-chat-panel {
  padding: 16px;
  border-radius: 22px;
  border: 1px solid rgba(10, 31, 68, 0.08);
  background: #fff;
}

.qa-link-button {
  border: 0;
  background: transparent;
  color: #234a78;
  cursor: pointer;
}

.qa-history-grid {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.qa-history-card,
.qa-status-card,
.qa-followup-chip,
.qa-trace-column {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(10, 31, 68, 0.08);
  background: #f7fafc;
}

.qa-history-card {
  text-align: left;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
}

.qa-history-card:hover,
.qa-history-card.active,
.qa-followup-chip:hover {
  transform: translateY(-1px);
  border-color: rgba(31, 78, 146, 0.2);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}

.qa-history-top span {
  font-size: 12px;
  color: var(--text-secondary);
}

.qa-history-card p,
.qa-empty-state {
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.qa-status-row {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.qa-status-card.live {
  background: linear-gradient(135deg, rgba(16, 42, 74, 0.96), rgba(29, 79, 139, 0.92));
  border-color: transparent;
}

.qa-status-card span {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.qa-status-card.live span,
.qa-status-card.live strong {
  color: #fff;
}

.qa-reasoning-detail {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 14px;
}

.qa-chat-head {
  margin-bottom: 14px;
}

.qa-chat-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.qa-chat-scroll {
  height: 540px;
  overflow: auto;
  padding: 10px 6px 10px 0;
  border-radius: 20px;
  border: 1px solid rgba(10, 31, 68, 0.08);
  background:
    radial-gradient(circle at top right, rgba(37, 89, 160, 0.08), transparent 20%),
    linear-gradient(180deg, #fbfdff, #f3f6fa);
}

.qa-chat-scroll :deep(.thread-timeline) {
  padding: 18px;
}

.qa-input-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 112px;
  gap: 12px;
  align-items: center;
  margin-top: 14px;
}

.qa-followup-row {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  margin-top: 14px;
}

.qa-followup-chip {
  text-align: left;
  cursor: pointer;
}

@media (max-width: 900px) {
  .qa-reasoning-detail,
  .qa-status-row,
  .qa-input-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .qa-console-head,
  .qa-history-head,
  .qa-reasoning-head,
  .qa-chat-head,
  .qa-history-top,
  .qa-trace-head {
    flex-direction: column;
    align-items: start;
  }

  .qa-console-actions {
    grid-auto-flow: row;
    justify-items: stretch;
  }

  .qa-chat-scroll {
    height: 460px;
  }
}
</style>
