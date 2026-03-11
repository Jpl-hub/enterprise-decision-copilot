<template>
  <section class="page-panel">
    <div class="panel-header-row">
      <div>
        <p class="section-tag">{{ eyebrow }}</p>
        <h2>{{ title }}</h2>
      </div>
      <slot name="actions" />
    </div>
    <p v-if="description" class="panel-description">{{ description }}</p>
    <slot />
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  eyebrow?: string;
  description?: string;
}>();
</script>
