<template>
  <div v-if="items?.length" class="evidence-list">
    <div v-for="(item, index) in items" :key="`${item.title}-${index}`" class="evidence-card">
      <div class="evidence-title-row">
        <strong>{{ item.title }}</strong>
        <span v-if="item.rerank_score !== undefined" class="badge-subtle">{{ item.rerank_score.toFixed(3) }}</span>
      </div>
      <p class="muted">{{ [item.report_date, item.institution || item.industry_name].filter(Boolean).join(' · ') }}</p>
      <p v-if="item.matched_excerpt" class="evidence-excerpt">{{ item.matched_excerpt }}</p>
      <a v-if="item.source_url" :href="item.source_url" target="_blank" rel="noreferrer">查看来源</a>
    </div>
  </div>
  <p v-else class="empty-state">暂无证据。</p>
</template>

<script setup lang="ts">
import type { EvidenceItem } from '../api/types';

defineProps<{
  items?: EvidenceItem[];
}>();
</script>
