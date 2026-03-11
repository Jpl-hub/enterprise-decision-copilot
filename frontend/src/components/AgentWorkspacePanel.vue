<template>
  <section class="agent-workspace-panel" :class="{ compact }">
    <div class="agent-workspace-head">
      <div>
        <p class="section-tag">{{ eyebrow }}</p>
        <h3>{{ title }}</h3>
      </div>
      <div class="button-row left-align">
        <RouterLink to="/threads" class="button-ghost compact-action">记录</RouterLink>
        <button class="button-ghost compact-action" @click="resetThread">新线程</button>
      </div>
    </div>

    <div class="task-mode-toggle-row">
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

    <div class="agent-input-shell">
      <input v-model="draft" class="text-input hero-input" :placeholder="placeholder" @keydown.enter="submit" />
      <button class="button-primary hero-button" @click="submit" :disabled="agentStore.loading">发送</button>
    </div>

    <div class="quick-prompt-row left-align" v-if="visiblePrompts.length">
      <button v-for="item in visiblePrompts" :key="item" class="button-ghost chip-button" @click="applyPrompt(item)">
        {{ item }}
      </button>
    </div>

    <div class="agent-mode-strip" v-if="agentStore.latest && !agentStore.loading">
      <span class="agent-mode-pill">{{ agentStore.latest.task_label }}</span>
      <span class="agent-mode-pill accent">{{ agentStore.latest.stage_label }}</span>
      <span v-for="item in agentStore.latest.deliverables.slice(0, compact ? 2 : 3)" :key="item" class="agent-mode-pill subtle">{{ item }}</span>
    </div>

    <div class="agent-workspace-body" v-if="agentStore.latest || agentStore.messages.length || agentStore.loading">
      <div class="agent-response-column">
        <div v-if="agentStore.loading" class="empty-state">正在分析...</div>
        <template v-else-if="agentStore.latest">
          <div class="answer-hero-card">
            <strong>{{ agentStore.latest.title }}</strong>
            <p>{{ agentStore.latest.summary }}</p>
          </div>
          <div v-for="item in agentStore.latest.highlights.slice(0, compact ? 3 : 5)" :key="item" class="answer-line-card">
            <p>{{ item }}</p>
          </div>
        </template>
      </div>

      <div class="agent-side-column">
        <div class="agent-mini-panel">
          <div class="trace-title-row">
            <strong>执行步骤</strong>
            <span class="badge-subtle" v-if="agentStore.focusCompanyName">{{ agentStore.focusCompanyName }}</span>
          </div>
          <TracePanel :trace="agentStore.latest?.plan" />
        </div>
        <div class="agent-mini-panel" v-if="agentStore.messages.length">
          <div class="trace-title-row">
            <strong>最近对话</strong>
            <span class="badge-subtle">{{ compact ? '最近 4 条' : '当前线程' }}</span>
          </div>
          <AgentThreadPanel :messages="messagePreview" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { RouterLink } from 'vue-router';

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
  { value: 'company_diagnosis', label: '企业诊断' },
  { value: 'company_risk_forecast', label: '风险预警' },
  { value: 'company_decision_brief', label: '决策建议' },
  { value: 'industry_trend', label: '行业趋势' },
  { value: 'data_quality', label: '数据治理' },
];

const agentStore = useAgentThreadStore();
const draft = ref(props.seedQuestion);
const activeTaskMode = computed(() => agentStore.taskMode || 'company_diagnosis');

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
      `这家公司有没有需要优先复核的问题？`,
      `当前数据底座会不会影响${companyName}的判断可信度？`,
    ],
  };
  return promptMap[activeTaskMode.value] || promptMap.company_diagnosis;
});

const visiblePrompts = computed(() => {
  if (agentStore.latest?.suggested_questions?.length) {
    return agentStore.latest.suggested_questions.slice(0, props.compact ? 3 : 4);
  }
  return basePrompts.value.slice(0, props.compact ? 2 : 3);
});

const messagePreview = computed(() => {
  return props.compact ? agentStore.messages.slice(-4) : agentStore.messages;
});

function resetThread() {
  agentStore.resetThread(props.companyCode, props.companyName);
  draft.value = props.seedQuestion || basePrompts.value[0];
}

function selectTaskMode(taskMode: string) {
  agentStore.setTaskMode(taskMode);
  draft.value = basePrompts.value[0];
}

function applyPrompt(text: string) {
  draft.value = text;
  void submit();
}

async function submit() {
  if (!draft.value.trim()) return;
  await agentStore.ask(draft.value.trim(), {
    companyCode: props.companyCode,
    companyName: props.companyName,
    taskMode: activeTaskMode.value,
  });
}

watch(() => props.seedQuestion, (value) => {
  if (value) {
    draft.value = value;
  }
}, { immediate: true });

watch(() => [props.companyCode, props.companyName], ([companyCode, companyName]) => {
  if (companyCode || companyName) {
    agentStore.setFocus(companyCode, companyName);
  }
});
</script>
