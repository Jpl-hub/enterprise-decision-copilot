<template>
  <section class="agent-workspace-panel notebook-agent-panel" :class="{ compact }">
    <div class="agent-workspace-head" :class="{ 'headless-workspace-head': !eyebrow && !title }">
      <div v-if="eyebrow || title">
        <p v-if="eyebrow" class="section-tag">{{ eyebrow }}</p>
        <h3 v-if="title">{{ title }}</h3>
      </div>
    </div>

    <div class="task-mode-toggle-row task-mode-toolbar">
      <div class="task-mode-pill-group">
        <button
          v-for="item in taskModes"
          :key="item.value"
          type="button"
          class="task-mode-toggle"
          :class="{ active: activeTaskMode === item.value }"
          @click="selectTaskMode(item.value)"
        >
          <span>{{ item.label }}</span>
        </button>
      </div>
      <button class="button-ghost compact-action task-mode-toolbar-action" @click="resetThread">新建线程</button>
    </div>

    <div class="agent-thread-shell">
      <div class="notebook-thread-block">
        <AgentThreadPanel :messages="messagePreview" />
      </div>

      <div v-if="agentStore.error" class="error-banner">
        {{ agentStore.error }}
      </div>

      <div v-if="agentStore.loading" class="answer-line-card pending-answer-card pending-chat-bubble">
        <p>正在整理分析结果，稍等片刻...</p>
      </div>

      <div class="agent-input-shell bottom-input-shell compact-bottom-input">
        <input v-model="draft" class="text-input hero-input" :placeholder="placeholder" @keydown.enter="submit" />
        <button class="button-primary hero-button" @click="submit" :disabled="agentStore.loading">发送</button>
      </div>

      <div class="notebook-starter-card compact-floating-starter" v-if="!hasConversation">
        <div class="quick-prompt-row left-align compact-prompt-row">
          <button v-for="item in starterPrompts" :key="item" class="button-ghost chip-button" @click="applyPrompt(item)">
            {{ item }}
          </button>
        </div>
      </div>

      <div v-if="floatingPanels.length" class="agent-insight-stack">
        <section v-for="panel in floatingPanels" :key="panel.key" class="agent-insight-card" :class="{ active: activeFloatingPanel === panel.key }">
          <button type="button" class="agent-insight-toggle" @click="toggleFloatingPanel(panel.key)">
            <strong>{{ panel.label }}</strong>
            <span>{{ activeFloatingPanel === panel.key ? '收起' : '展开' }}</span>
          </button>

          <div v-if="activeFloatingPanel === panel.key" class="agent-insight-body">
            <div v-if="panel.key === 'summary' && agentStore.latest" class="floating-panel-body">
              <div class="agent-mode-strip">
                <span class="agent-mode-pill accent">{{ agentStore.latest.stage_label }}</span>
                <span v-for="item in agentStore.latest.deliverables.slice(0, compact ? 2 : 3)" :key="item" class="agent-mode-pill subtle">{{ item }}</span>
              </div>
              <div class="agent-output-grid" v-if="outputCards.length">
                <div v-for="item in outputCards" :key="item.label" class="agent-output-card">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                </div>
              </div>
              <div class="answer-hero-card">
                <strong>{{ agentStore.latest.title }}</strong>
                <p>{{ agentStore.latest.summary }}</p>
              </div>
              <div v-for="item in agentStore.latest.highlights.slice(0, compact ? 3 : 5)" :key="item" class="answer-line-card">
                <p>{{ item }}</p>
              </div>
            </div>

            <div v-else-if="panel.key === 'plan' && agentStore.latest?.plan?.length" class="floating-panel-body">
              <TracePanel :trace="agentStore.latest.plan" />
            </div>

            <div v-else-if="panel.key === 'route' && routeCandidates.length" class="floating-panel-body">
              <div class="agent-route-list">
                <article v-for="item in routeCandidates" :key="`${item.intent}-${item.score}`" class="agent-route-card">
                  <div class="agent-route-top">
                    <div>
                      <span class="agent-route-label">{{ item.label }}</span>
                      <strong class="agent-route-score">评分 {{ item.score.toFixed(1) }}</strong>
                    </div>
                    <span class="agent-route-chip">{{ item.intent }}</span>
                  </div>
                  <p class="agent-route-reasons">{{ item.reasons.join('；') || '当前按默认链路进入。' }}</p>
                </article>
              </div>
            </div>

            <div v-else-if="panel.key === 'followup' && followUpQuestions.length" class="floating-panel-body">
              <div class="follow-up-stack">
                <button v-for="item in followUpQuestions" :key="item" class="follow-up-card" @click="applyPrompt(item)">
                  {{ item }}
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

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

const agentStore = useAgentThreadStore();
const draft = ref(props.seedQuestion);
const manualTaskMode = ref<string | null>(null);
const activeFloatingPanel = ref<'summary' | 'plan' | 'route' | 'followup' | null>(null);
const activeTaskMode = computed(() => manualTaskMode.value || agentStore.taskMode || 'company_diagnosis');

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
const routeCandidates = computed(() => agentStore.latest?.route_candidates?.slice(0, props.compact ? 2 : 3) || []);
const hasConversation = computed(() => agentStore.messages.length > 0);
const messagePreview = computed(() => props.compact ? agentStore.messages.slice(-4) : agentStore.messages);

const floatingPanels = computed(() => {
  const panels: Array<{ key: 'summary' | 'plan' | 'route' | 'followup'; label: string }> = [];
  if (agentStore.latest) panels.push({ key: 'summary', label: '本轮结论' });
  if (agentStore.latest?.plan?.length) panels.push({ key: 'plan', label: '执行步骤' });
  if (routeCandidates.value.length) panels.push({ key: 'route', label: '分析路径' });
  if (followUpQuestions.value.length) panels.push({ key: 'followup', label: '推荐追问' });
  return panels;
});

const outputCards = computed(() => {
  const latest = agentStore.latest;
  if (!latest) return [];
  const cards = [
    { label: '任务模式', value: latest.task_label },
    { label: '当前阶段', value: latest.stage_label },
  ];
  const evidence = latest.evidence || {};
  if (latest.task_mode === 'company_risk_forecast') {
    const model = evidence.model_prediction as Record<string, unknown> | undefined;
    const probability = typeof model?.high_risk_probability === 'number' ? `${(model.high_risk_probability * 100).toFixed(1)}%` : '同步中';
    cards.push({ label: '高风险概率', value: probability });
  } else if (latest.task_mode === 'company_compare') {
    const companies = (evidence.companies as unknown[] | undefined)?.length || 0;
    cards.push({ label: '对比企业', value: `${companies} 家` });
  } else if (latest.task_mode === 'data_quality') {
    const anomalies = (evidence.top_anomalies as unknown[] | undefined)?.length || 0;
    cards.push({ label: '异常条目', value: `${anomalies} 条` });
  } else {
    cards.push({ label: '结论要点', value: `${latest.highlights.length} 条` });
  }
  return cards;
});

function resetThread() {
  manualTaskMode.value = null;
  agentStore.resetThread(props.companyCode, props.companyName);
  draft.value = props.seedQuestion || basePrompts.value[0];
  activeFloatingPanel.value = null;
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

function toggleFloatingPanel(key: 'summary' | 'plan' | 'route' | 'followup') {
  activeFloatingPanel.value = activeFloatingPanel.value === key ? null : key;
}

async function submit() {
  const question = draft.value.trim();
  if (!question) return;
  await agentStore.ask(question, {
    companyCode: props.companyCode,
    companyName: props.companyName,
    taskMode: manualTaskMode.value ?? undefined,
  });
  draft.value = '';
}

watch(() => props.seedQuestion, (value) => {
  if (value) {
    draft.value = value;
  }
}, { immediate: true });

watch(() => [props.companyCode, props.companyName], ([companyCode, companyName]) => {
  manualTaskMode.value = null;
  if (companyCode || companyName) {
    agentStore.setFocus(companyCode, companyName);
  }
});

watch(floatingPanels, (panels) => {
  if (!panels.length || !panels.some((item) => item.key === activeFloatingPanel.value)) {
    activeFloatingPanel.value = null;
  }
}, { immediate: true });
</script>
