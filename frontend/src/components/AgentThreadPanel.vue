<template>
  <div v-if="messages?.length" class="thread-timeline">
    <div v-for="(item, index) in messages" :key="`${item.created_at}-${index}`" class="thread-message" :class="item.role">
      <div class="thread-message-meta">
        <strong>{{ item.role === 'user' ? '你' : 'Agent' }}</strong>
        <span>{{ item.created_at }}</span>
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
</script>
