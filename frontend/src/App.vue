<template>
  <div class="app-shell">
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
      <div class="header-note">
        <span class="status-dot"></span>
        <span>选企业、提问题、看证据、拿建议动作</span>
      </div>
    </header>

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router';
</script>
