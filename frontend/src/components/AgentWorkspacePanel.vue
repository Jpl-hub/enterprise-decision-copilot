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

    <div class="agent-input-shell">
      <input v-model="draft" class="text-input hero-input" :placeholder="placeholder" @keydown.enter="submit" />
      <button class="button-primary hero-button" @click="submit" :disabled="agentStore.loading">发送</button>
    </div>

    <div class="quick-prompt-row left-align" v-if="visiblePrompts.length">
      <button v-for="item in visiblePrompts" :key="item" class="button-ghost chip-button" @click="applyPrompt(item)">
        {{ item }}
      </button>
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

const agentStore = useAgentThreadStore();
const draft = ref(props.seedQuestion);

const basePrompts = computed(() => {
  const companyName = props.companyName || '这家公司';
  return [
    `${companyName}当前最值得关注的经营问题是什么？`,
    `把${companyName}的风险拆成财务、经营、行业三层`,
    `${companyName}和同行相比最强和最弱的地方是什么？`,
  ];
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

function applyPrompt(text: string) {
  draft.value = text;
  void submit();
}

async function submit() {
  if (!draft.value.trim()) return;
  await agentStore.ask(draft.value.trim(), {
    companyCode: props.companyCode,
    companyName: props.companyName,
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
