<template>
  <div v-if="route.name === 'login'" class="app-shell auth-layout">
    <main class="app-main auth-main">
      <RouterView />
    </main>
  </div>
  <div v-else class="app-shell">
    <header class="app-header refined-header">
      <div class="brand-block compact-brand-block">
        <p class="eyebrow">Enterprise Decision Intelligence</p>
        <div class="brand-title-row">
          <h1>企智策源</h1>
          <span class="brand-pill">Agent + Data + AI</span>
        </div>
      </div>

      <nav class="top-nav refined-top-nav">
        <RouterLink to="/" class="nav-chip">开始分析</RouterLink>
        <RouterLink to="/workbench" class="nav-chip">企业分析</RouterLink>
        <RouterLink to="/compare" class="nav-chip">企业对比</RouterLink>
        <RouterLink to="/quality" class="nav-chip">数据治理</RouterLink>
        <RouterLink to="/threads" class="nav-chip">分析记录</RouterLink>
      </nav>

      <div class="header-user-actions refined-user-actions" v-if="authStore.user">
        <span class="user-identity">{{ authStore.user.display_name }}</span>
        <RouterLink v-if="authStore.canViewAudit" to="/audit" class="button-ghost compact-action">审计</RouterLink>
        <button class="button-ghost compact-action" @click="logout">退出</button>
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
