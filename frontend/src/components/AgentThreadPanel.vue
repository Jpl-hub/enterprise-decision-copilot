<template>
  <div v-if="messages?.length" class="thread-timeline chat-bubble-timeline">
    <div v-for="(item, index) in messages" :key="`${item.created_at}-${index}`" class="thread-message-row" :class="item.role">
      <div class="thread-message-avatar">{{ item.role === 'user' ? '你' : 'A' }}</div>
      <div class="thread-message" :class="item.role">
        <div class="thread-message-meta">
          <strong>{{ item.role === 'user' ? '你' : 'Agent' }}</strong>
          <span>{{ formatTime(item.created_at) }}</span>
        </div>
        <div class="thread-message-body">
          <p v-for="(line, lineIndex) in splitContent(item.content)" :key="`${item.created_at}-${lineIndex}`" :class="{ bullet: line.startsWith('- ') }">
            {{ normalizeLine(line) }}
          </p>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="thread-empty-state">
    <p>开始提问。</p>
  </div>
</template>

<script setup lang="ts">
import type { AgentThreadMessage } from '../api/types';

defineProps<{
  messages?: AgentThreadMessage[];
}>();

function formatTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function splitContent(value: string) {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalizeLine(value: string) {
  return value.startsWith('- ') ? value.slice(2) : value;
}
</script>
