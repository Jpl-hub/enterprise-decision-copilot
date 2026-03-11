<template>
  <div v-if="route.name === 'login'" class="app-shell auth-layout">
    <main class="app-main auth-main">
      <RouterView />
    </main>
  </div>
  <div v-else class="app-shell">
    <header class="app-header">
      <div class="brand-block">
        <p class="eyebrow">Enterprise Decision Intelligence</p>
        <div class="brand-title-row">
          <h1>企智策源</h1>
          <span class="brand-pill">企业决策系统</span>
        </div>
        <p class="brand-subtitle">用真实资料回答企业经营问题，而不是只给一段模型输出。</p>
      </div>
      <nav class="top-nav">
        <RouterLink to="/" class="nav-chip">开始分析</RouterLink>
        <RouterLink to="/workbench" class="nav-chip">企业分析</RouterLink>
        <RouterLink to="/compare" class="nav-chip">企业对比</RouterLink>
        <RouterLink to="/quality" class="nav-chip">数据治理</RouterLink>
      </nav>
      <div class="header-note header-user-bar">
        <div class="header-note-inline">
          <span class="status-dot"></span>
          <span>选企业、提问题、看证据、拿建议动作</span>
        </div>
        <div class="header-user-actions" v-if="authStore.user">
          <span>{{ authStore.user.display_name }} · {{ authStore.user.role }}</span>
          <button class="button-ghost" @click="logout">退出登录</button>
        </div>
      </div>
    </header>

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter, useRoute, RouterLink, RouterView } from 'vue-router';

import { useAuthStore } from './stores/auth';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

onMounted(async () => {
  await authStore.restoreSession();
  if (!authStore.user && route.name !== 'login') {
    await router.replace({ name: 'login' });
  }
});

async function logout() {
  await authStore.logout();
  await router.replace({ name: 'login' });
}
</script>
