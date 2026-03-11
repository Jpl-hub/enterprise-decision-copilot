<template>
  <div class="page-stack audit-page">
    <PagePanel title="操作审计" eyebrow="Audit" description="记录关键操作，方便回看谁导出了材料、谁提交了复核、谁发起了分析。">
      <template #actions>
        <div class="toolbar-cluster">
          <select v-model="limit" class="select-input toolbar-select">
            <option :value="20">最近 20 条</option>
            <option :value="50">最近 50 条</option>
            <option :value="100">最近 100 条</option>
          </select>
          <button class="button-primary" @click="loadLogs">刷新日志</button>
        </div>
      </template>

      <div v-if="!authStore.canViewAudit" class="empty-state">当前账号只能查看业务页面，审计日志仅对管理员开放。</div>
      <div v-else-if="loading" class="empty-state">正在加载操作日志...</div>
      <div v-else-if="logs.length" class="stack-list">
        <div v-for="item in logs" :key="item.log_id" class="info-card compact audit-log-card">
          <div class="trace-title-row">
            <strong>{{ eventLabel(item.event_type) }}</strong>
            <span class="badge-subtle">{{ item.created_at }}</span>
          </div>
          <p class="muted">用户 {{ item.user_id || 'unknown' }} · {{ item.target_type || 'target' }} · {{ item.target_id || 'n/a' }}</p>
          <p class="muted">{{ detailText(item.detail) }}</p>
        </div>
      </div>
      <div v-else class="empty-state">暂时没有审计记录。</div>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';

import { api } from '../api/client';
import type { AuditLogItem } from '../api/types';
import PagePanel from '../components/PagePanel.vue';
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();
const loading = ref(false);
const limit = ref(20);
const logs = ref<AuditLogItem[]>([]);

function eventLabel(eventType: string) {
  const labels: Record<string, string> = {
    'auth.login': '用户登录',
    'auth.register': '用户注册',
    'auth.logout': '退出登录',
    'agent.query': '发起分析',
    'quality.review.submit': '提交复核',
    'quality.review.auto_sync': '自动生成复核任务',
    'competition.package.export': '导出分析材料',
  };
  return labels[eventType] || eventType;
}

function detailText(detail: Record<string, unknown>) {
  return Object.entries(detail)
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(' · ') || '无附加说明';
}

async function loadLogs() {
  if (!authStore.canViewAudit) return;
  loading.value = true;
  try {
    const payload = await api.getAuditLogs(limit.value);
    logs.value = payload.items;
  } finally {
    loading.value = false;
  }
}

watch(limit, () => {
  void loadLogs();
});

onMounted(() => {
  void loadLogs();
});
</script>
