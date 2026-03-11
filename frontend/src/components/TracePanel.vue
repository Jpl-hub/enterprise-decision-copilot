<template>
  <div v-if="trace?.length" class="trace-list">
    <div v-for="(item, index) in trace" :key="`${item.step}-${index}`" class="trace-card">
      <div class="trace-title-row">
        <strong>{{ item.step }}</strong>
        <span class="badge-subtle">{{ item.status }}</span>
      </div>
      <p class="muted">{{ item.detail }}</p>
    </div>
  </div>
  <p v-else class="empty-state">暂无执行轨迹。</p>
</template>

<script setup lang="ts">
import type { AgentTraceStep } from '../api/types';

defineProps<{
  trace?: AgentTraceStep[];
}>();
</script>
