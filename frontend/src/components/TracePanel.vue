<template>
  <div v-if="trace?.length" class="trace-list">
    <div v-for="(item, index) in trace" :key="`${item.step}-${index}`" class="trace-card">
      <div class="trace-title-row">
        <strong>{{ formatStep(item.step) }}</strong>
        <span class="badge-subtle">{{ formatStatus(item.status) }}</span>
      </div>
      <p>{{ item.detail }}</p>
    </div>
  </div>
  <p v-else class="empty-state">暂无执行步骤。</p>
</template>

<script setup lang="ts">
import type { AgentTraceStep } from '../api/types';

const props = defineProps<{
  trace?: AgentTraceStep[];
}>();

const stepLabels: Record<string, string> = {
  problem_intake: '接收问题',
  entity_resolution: '锁定对象',
  intent_planning: '判断任务类型',
  data_readiness: '检查数据状态',
  comparison_scope: '确认对比范围',
  comparison_evidence: '抽取横向证据',
  quality_scope: '检查数据覆盖',
  review_queue: '整理待处理问题',
  risk_features: '提取风险特征',
  risk_scoring: '生成风险判断',
  company_evidence: '汇总企业证据',
  decision_synthesis: '形成经营判断',
  industry_digest: '整理行业资料',
  overview_digest: '汇总全局信息',
  fallback_guidance: '问题引导',
  tool_selection: '选择分析路径',
  answer_synthesis: '输出结果',
};

const statusLabels: Record<string, string> = {
  completed: '已完成',
  pending: '待执行',
  running: '进行中',
};

function formatStep(step: string) {
  return stepLabels[step] || step;
}

function formatStatus(status: string) {
  return statusLabels[status] || status;
}
</script>
