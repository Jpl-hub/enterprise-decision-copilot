<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div>
        <p class="eyebrow">Agent + Data + AI</p>
        <h1>企航数策 Console</h1>
        <p class="sidebar-text">前后端分离版本的运营分析与决策支持系统，面向比赛演示和后续扩展。</p>
      </div>
      <nav class="nav-list">
        <RouterLink to="/" class="nav-item">系统总览</RouterLink>
        <RouterLink to="/compare" class="nav-item">企业对比驾驶舱</RouterLink>
        <RouterLink to="/workbench" class="nav-item">企业工作台</RouterLink>
        <RouterLink to="/quality" class="nav-item">数据质量中台</RouterLink>
        <RouterLink to="/competition" class="nav-item">答辩稿工作台</RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router';
</script>
