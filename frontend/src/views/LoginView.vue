<template>
  <div class="login-shell refined-login-shell">
    <div class="login-panel refined-login-panel">
      <div class="login-brand-block">
        <p class="section-tag">Secure Access</p>
        <h1>登录企智策源</h1>
        <div class="login-capability-row">
          <span>分析记录</span>
          <span>导出材料</span>
          <span>团队权限</span>
        </div>
      </div>

      <div class="login-tabs">
        <button class="button-ghost" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button class="button-ghost" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <div class="stack-list top-gap">
        <input v-model="displayName" class="text-input" placeholder="显示名称" v-if="mode === 'register'" />
        <input v-model="username" class="text-input" placeholder="用户名" />
        <input v-model="password" class="text-input" type="password" placeholder="密码" @keydown.enter="submit" />
      </div>

      <div class="button-row top-gap left-align">
        <button class="button-primary login-submit-button" @click="submit" :disabled="authStore.loading">
          {{ mode === 'login' ? '进入系统' : '创建账号' }}
        </button>
      </div>

      <p v-if="authStore.error" class="error-box top-gap">{{ authStore.error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const mode = ref<'login' | 'register'>('login');
const username = ref('');
const displayName = ref('');
const password = ref('');

async function submit() {
  if (!username.value.trim() || !password.value.trim()) return;
  if (mode.value === 'register') {
    await authStore.register(username.value.trim(), displayName.value.trim() || username.value.trim(), password.value.trim());
  } else {
    await authStore.login(username.value.trim(), password.value.trim());
  }
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/';
  await router.replace(redirect);
}
</script>
