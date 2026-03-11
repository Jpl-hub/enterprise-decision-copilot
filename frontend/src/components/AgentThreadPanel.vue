<template>
  <div v-if="messages?.length" class="thread-timeline">
    <div v-for="(item, index) in messages" :key="`${item.created_at}-${index}`" class="thread-message" :class="item.role">
      <div class="thread-message-meta">
        <strong>{{ item.role === 'user' ? '你' : 'Agent' }}</strong>
        <span>{{ formatTime(item.created_at) }}</span>
      </div>
      <p>{{ item.content }}</p>
    </div>
  </div>
  <p v-else class="empty-state">当前线程还没有对话记录。</p>
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
</script>
