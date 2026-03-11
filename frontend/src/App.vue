<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="brand-block">
        <p class="eyebrow">Enterprise Decision Intelligence</p>
        <div class="brand-title-row">
          <h1>企智策源</h1>
          <span class="brand-pill">企业决策系统</span>
        </div>
        <p class="brand-subtitle">智能体驱动的企业运营分析与决策支持系统</p>
      </div>
      <nav class="top-nav">
        <RouterLink to="/" class="nav-chip">Agent 指挥台</RouterLink>
        <RouterLink to="/workbench" class="nav-chip">企业分析</RouterLink>
        <RouterLink to="/compare" class="nav-chip">企业对比</RouterLink>
        <RouterLink to="/quality" class="nav-chip">数据治理</RouterLink>
      </nav>
      <div class="header-note">
        <span class="status-dot"></span>
        <span>真实数据、可追溯证据、多模态抽取、风险模型联动</span>
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
