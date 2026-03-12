<template>
  <div class="page-stack">
    <PagePanel title="分析记录" eyebrow="Analysis Threads" description="回看最近的分析线程，恢复上下文后继续追问，不用从头再来。">
      <template #actions>
        <button class="button-ghost" @click="refreshHistory" :disabled="agentStore.loadingHistory">刷新记录</button>
      </template>

      <div class="panel-split two-cols top-gap thread-library-layout">
        <div class="sub-panel">
          <div class="sub-panel-header">
            <h3>最近线程</h3>
            <span class="badge-subtle">{{ agentStore.history.length }} 条</span>
          </div>
          <div v-if="agentStore.loadingHistory" class="empty-state">正在加载分析记录...</div>
          <div v-else-if="!agentStore.history.length" class="empty-state">还没有历史线程，先去开始分析提一个问题。</div>
          <div v-else class="stack-list">
            <button
              v-for="item in agentStore.history"
              :key="item.thread_id"
              type="button"
              class="thread-record-card"
              :class="{ active: agentStore.threadId === item.thread_id }"
              @click="openThread(item.thread_id)"
            >
              <div class="thread-record-header">
                <strong>{{ item.title }}</strong>
                <span>{{ formatDate(item.updated_at) }}</span>
              </div>
              <p>{{ item.thread_summary || item.last_message || '本线程还没有摘要。' }}</p>
              <div class="thread-record-meta">
                <span>{{ item.focus?.company_name || '未固定企业' }}</span>
                <span>{{ item.message_count }} 条消息</span>
              </div>
            </button>
          </div>
        </div>

        <div class="sub-panel">
          <div class="sub-panel-header">
            <h3>线程详情</h3>
            <RouterLink to="/">回到开始分析</RouterLink>
          </div>
          <div v-if="!agentStore.threadId" class="empty-state">选择左侧任意线程后，这里会显示完整上下文。</div>
          <div v-else class="stack-list">
            <div class="thread-header">
              <div>
                <strong>{{ agentStore.threadTitle }}</strong>
                <p>当前对象：{{ agentStore.focusCompanyName || '未固定企业' }}</p>
              </div>
              <button class="button-ghost" @click="goOverview">继续追问</button>
            </div>
            <div v-if="agentStore.threadMemory || agentStore.threadSummary" class="info-card compact section-card">
              <strong>线程记忆</strong>
              <p v-if="agentStore.threadSummary">{{ agentStore.threadSummary }}</p>
              <p v-if="agentStore.threadMemory?.conclusion">结论：{{ agentStore.threadMemory.conclusion }}</p>
              <p v-if="agentStore.threadMemory?.key_signals?.length">关键点：{{ agentStore.threadMemory.key_signals.join('；') }}</p>
              <p v-if="agentStore.threadMemory?.evidence_focus?.length">证据焦点：{{ agentStore.threadMemory.evidence_focus.join('、') }}</p>
              <p v-if="agentStore.threadMemory?.next_steps?.length">下一步：{{ agentStore.threadMemory.next_steps.join('；') }}</p>
            </div>
            <AgentThreadPanel :messages="agentStore.messages" />
          </div>
        </div>
      </div>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

import AgentThreadPanel from '../components/AgentThreadPanel.vue';
import PagePanel from '../components/PagePanel.vue';
import { useAgentThreadStore } from '../stores/agentThread';

const agentStore = useAgentThreadStore();
const router = useRouter();

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

async function refreshHistory() {
  await agentStore.loadHistory();
}

async function openThread(threadId: string) {
  await agentStore.openThread(threadId);
}

async function goOverview() {
  await router.push({ name: 'overview' });
}

onMounted(async () => {
  await refreshHistory();
});
</script>
