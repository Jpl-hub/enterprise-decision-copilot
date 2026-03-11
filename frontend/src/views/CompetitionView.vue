<template>
  <div class="page-stack">
    <PagePanel title="分析材料导出" eyebrow="Report Export" description="为单家企业生成结构化分析材料、引用清单和本地证据包。">
      <template #actions>
        <select v-model="selectedCode" class="select-input">
          <option v-for="item in targets" :key="item.company_code" :value="item.company_code">{{ item.company_name }}</option>
        </select>
      </template>
      <div v-if="!authStore.canExport" class="empty-state">当前账号可以查看分析页面，如需导出材料，请联系分析员或管理员。</div>
      <template v-else>
        <div class="button-row">
          <input v-model="question" class="text-input flex-grow" placeholder="结合真实数据生成企业运营分析材料" />
          <button class="button-primary" @click="loadPackage">导出材料</button>
        </div>
        <div v-if="loading" class="empty-state">正在生成分析材料...</div>
        <div v-else-if="result" class="page-stack">
          <div class="metrics-grid">
            <MetricCard label="引用条数" :value="result.citation_count" />
            <MetricCard label="报告年度" :value="result.report_year" />
            <MetricCard label="公司代码" :value="result.company_code" />
            <MetricCard label="导出时间" :value="result.exported_at.slice(0, 10)" />
          </div>
          <div class="panel-split two-cols">
            <div class="sub-panel">
              <h3>章节提纲</h3>
              <div class="stack-list">
                <div v-for="section in result.sections" :key="section.title" class="info-card compact">
                  <strong>{{ section.title }}</strong>
                  <p class="muted">{{ section.content }}</p>
                </div>
              </div>
            </div>
            <div class="sub-panel">
              <h3>引用证据</h3>
              <div class="stack-list">
                <div v-for="item in result.citations" :key="item.citation_id" class="info-card compact">
                  <div class="trace-title-row">
                    <strong>[{{ item.citation_id }}] {{ item.title }}</strong>
                    <span class="badge-subtle">{{ item.source_type }}</span>
                  </div>
                  <p class="muted">{{ [item.report_date, item.institution].filter(Boolean).join(' · ') }}</p>
                </div>
              </div>
            </div>
          </div>
          <div class="sub-panel">
            <h3>导出文件</h3>
            <p class="muted">Markdown：{{ result.markdown_path || '未落盘' }}</p>
            <p class="muted">证据包：{{ result.evidence_path || '未落盘' }}</p>
            <pre class="markdown-preview">{{ result.markdown_content }}</pre>
          </div>
        </div>
      </template>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import { api } from '../api/client';
import type { CompetitionPackageResponse } from '../api/types';
import MetricCard from '../components/MetricCard.vue';
import PagePanel from '../components/PagePanel.vue';
import { useAuthStore } from '../stores/auth';
import { useDashboardStore } from '../stores/dashboard';

const props = defineProps<{ companyCode?: string }>();
const route = useRoute();
const authStore = useAuthStore();
const store = useDashboardStore();
const selectedCode = ref(props.companyCode || '');
const question = ref('结合真实数据生成企业运营分析材料');
const loading = ref(false);
const result = ref<CompetitionPackageResponse | null>(null);
const targets = computed(() => store.targets);

async function loadTargets() {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  if (!selectedCode.value && store.targets.length) {
    selectedCode.value = props.companyCode || String(route.params.companyCode || store.targets[0].company_code);
  }
}

async function loadPackage() {
  if (!selectedCode.value || !authStore.canExport) return;
  loading.value = true;
  try {
    const companyName = targets.value.find((item) => item.company_code === selectedCode.value)?.company_name || '该企业';
    result.value = await api.getCompetitionPackage(selectedCode.value, question.value || `结合真实数据为${companyName}生成企业运营分析材料`, true);
  } finally {
    loading.value = false;
  }
}

watch(() => props.companyCode, (value) => {
  if (value) selectedCode.value = value;
});

onMounted(async () => {
  await loadTargets();
  if (selectedCode.value && authStore.canExport) {
    await loadPackage();
  }
});
</script>
