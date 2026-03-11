<template>
  <div class="metric-card">
    <span>{{ label }}</span>
    <strong>{{ value }}</strong>
    <p v-if="hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  hint?: string;
}>();
</script>
