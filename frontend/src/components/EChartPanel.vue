<template>
  <div ref="container" class="echart-panel" :style="{ height }"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue';
import type { ECharts, EChartsCoreOption } from 'echarts';

const props = withDefaults(defineProps<{
  option: EChartsCoreOption;
  height?: string;
}>(), {
  height: '320px',
});

const emit = defineEmits<{
  chartClick: [params: Record<string, unknown>];
}>();

const container = ref<HTMLDivElement | null>(null);
const chart = shallowRef<ECharts | null>(null);
let resizeObserver: ResizeObserver | null = null;

async function renderChart() {
  if (!container.value) return;
  const echarts = await import('echarts');
  if (!chart.value) {
    chart.value = echarts.init(container.value);
    chart.value.on('click', (params) => {
      emit('chartClick', params as Record<string, unknown>);
    });
  }
  chart.value.setOption(props.option, true);
  chart.value.resize();
}

onMounted(() => {
  void renderChart();
  if (container.value) {
    resizeObserver = new ResizeObserver(() => {
      chart.value?.resize();
    });
    resizeObserver.observe(container.value);
  }
});

watch(() => props.option, () => {
  void renderChart();
}, { deep: true });

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  resizeObserver = null;
  chart.value?.dispose();
  chart.value = null;
});
</script>
