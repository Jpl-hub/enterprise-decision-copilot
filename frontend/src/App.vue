<template>
  <div v-if="route.name === 'login'" class="app-shell auth-layout">
    <main class="app-main auth-main">
      <RouterView />
    </main>
  </div>
  <div v-else class="app-shell">
    <header class="app-header refined-header">
      <div class="brand-block compact-brand-block">
        <div class="brand-title-row">
          <h1>企智策源</h1>
          <span class="brand-pill">Agent + Data + AI</span>
        </div>
      </div>

      <nav class="top-nav refined-top-nav">
        <RouterLink to="/" class="nav-chip" exact-active-class="nav-chip-exact-active">开始分析</RouterLink>
        <RouterLink to="/workbench" class="nav-chip">企业分析</RouterLink>
        <RouterLink to="/compare" class="nav-chip">企业对比</RouterLink>
        <RouterLink to="/quality" class="nav-chip">数据治理</RouterLink>
      </nav>

      <details class="user-menu" v-if="authStore.user">
        <summary class="user-menu-trigger">
          <span class="user-avatar">{{ userInitial }}</span>
          <span class="user-role">{{ roleLabel }}</span>
        </summary>
        <div class="user-menu-panel">
          <div class="user-menu-meta">
            <strong>{{ authStore.user.display_name }}</strong>
            <span>{{ roleLabel }}</span>
          </div>
          <RouterLink to="/threads" class="user-menu-link">分析记录</RouterLink>
          <RouterLink v-if="authStore.canViewAudit" to="/audit" class="user-menu-link">操作审计</RouterLink>
          <button class="user-menu-link danger" @click="logout">退出登录</button>
        </div>
      </details>
    </header>

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter, useRoute, RouterLink, RouterView } from 'vue-router';

import { useAuthStore } from './stores/auth';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const roleLabel = computed(() => {
  if (authStore.role === 'admin') return '管理员';
  if (authStore.role === 'analyst') return '分析员';
  return '查看者';
});

const userInitial = computed(() => authStore.user?.display_name?.slice(0, 1) || '我');

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
