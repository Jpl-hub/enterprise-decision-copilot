<template>
  <div class="page-stack overview-page">
    <section class="hero-panel">
      <div class="hero-copy">
        <p class="section-tag">Start Here</p>
        <h2>先选企业，再把问题交给系统。</h2>
        <p class="hero-text">
          你可以直接问经营质量、竞争格局、风险变化和后续动作。系统会把财报、研报、宏观指标和图表表格里的关键信息组织成一份可追溯结论。
        </p>
        <div class="hero-command company-question-row">
          <select v-model="selectedCode" class="select-input hero-select">
            <option v-for="item in store.targets" :key="item.company_code" :value="item.company_code">{{ item.company_name }}</option>
          </select>
          <input
            v-model="question"
            class="text-input hero-input"
            placeholder="例如：这家公司未来两年的主要风险和机会是什么？"
            @keydown.enter="runAgent"
          />
          <button class="button-primary hero-button" @click="runAgent" :disabled="agentLoading">开始分析</button>
        </div>
        <div class="quick-prompt-row">
          <button v-for="prompt in quickPrompts" :key="prompt" class="button-ghost chip-button" @click="applyPrompt(prompt)">
            {{ prompt }}
          </button>
        </div>
      </div>
      <div class="hero-side">
        <div class="hero-highlight-card">
          <p class="section-tag">你可以直接问</p>
          <ul class="hero-list">
            <li>这家公司现在更值得扩张、观望还是重点防风险？</li>
            <li>和同行相比，它的盈利、成长和研发投入处在什么位置？</li>
            <li>这份结论分别来自哪些财报字段、研报观点和宏观信号？</li>
          </ul>
        </div>
        <div class="hero-stat-strip" v-if="store.payload?.metrics">
          <div class="hero-stat">
            <span>企业样本</span>
            <strong>{{ store.payload.metrics.sample_count }}</strong>
          </div>
          <div class="hero-stat">
            <span>个股研报</span>
            <strong>{{ store.payload.metrics.research_report_count }}</strong>
          </div>
          <div class="hero-stat">
            <span>行业研报</span>
            <strong>{{ store.payload.metrics.industry_report_count }}</strong>
          </div>
        </div>
      </div>
    </section>

    <section class="three-card-grid">
      <RouterLink to="/workbench" class="capability-card capability-card-agent">
        <p class="section-tag">单家公司</p>
        <h3>我想看一家企业现在是什么状态</h3>
        <p>进入企业分析页，直接拿到经营结论、风险画像、关键证据和可继续追问的线程。</p>
      </RouterLink>
      <RouterLink to="/compare" class="capability-card capability-card-compare">
        <p class="section-tag">多家公司</p>
        <h3>我想知道谁更值得重点跟踪</h3>
        <p>对比盈利、成长、研发和风险，不用自己在多张表之间来回切换。</p>
      </RouterLink>
      <RouterLink to="/quality" class="capability-card capability-card-data">
        <p class="section-tag">可信度</p>
        <h3>我想确认数据够不够全、结论靠不靠谱</h3>
        <p>查看官方资料覆盖、抽取质量和待复核问题，判断结果是否可直接使用。</p>
      </RouterLink>
    </section>

    <PagePanel title="当前分析结果" eyebrow="Answer" description="先给判断，再给来源，再告诉你下一步还能怎么问。">
      <div v-if="agentLoading" class="empty-state">正在整合资料并生成结论...</div>
      <div v-else-if="agentResult" class="panel-split two-cols agent-answer-grid">
        <div class="sub-panel emphasis-panel">
          <p class="section-tag">结论</p>
          <h3>{{ agentResult.title }}</h3>
          <p class="panel-description strong-copy">{{ agentResult.summary }}</p>
          <div class="stack-list" v-if="agentResult.highlights.length">
            <div v-for="item in agentResult.highlights.slice(0, 5)" :key="item" class="info-card compact answer-card">
              <p>{{ item }}</p>
            </div>
          </div>
          <div class="stack-list" v-if="agentResult.suggested_questions?.length">
            <div class="info-card compact suggestion-block">
              <strong>下一步可以继续问</strong>
              <div class="quick-prompt-row left-align top-gap">
                <button
                  v-for="item in agentResult.suggested_questions.slice(0, 3)"
                  :key="item"
                  class="button-ghost chip-button"
                  @click="applyPrompt(item)"
                >
                  {{ item }}
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="sub-panel">
          <p class="section-tag">本次调用</p>
          <TracePanel :trace="agentResult.trace" />
        </div>
      </div>
      <div v-else class="empty-state">输入一个问题，系统会自动组织企业分析、研报检索、风险评估和可信度检查。</div>
    </PagePanel>

    <PagePanel title="这些结论来自哪里" eyebrow="Sources" description="系统先理解资料，再生成答案。技术细节藏在后面，证据链留给你核对。">
      <div class="source-grid">
        <div class="source-card">
          <p class="section-tag">官方财报</p>
          <h3>{{ qualitySummary ? `${qualitySummary.official_report_downloaded_slots} / ${qualitySummary.official_report_expected_slots}` : '加载中' }}</h3>
          <p class="muted">来自交易所披露的正式年报，覆盖率越高，经营分析越完整。</p>
        </div>
        <div class="source-card">
          <p class="section-tag">研究报告</p>
          <h3>{{ store.payload?.metrics ? store.payload.metrics.research_report_count + store.payload.metrics.industry_report_count : '加载中' }}</h3>
          <p class="muted">个股研报和行业研报一起提供市场观点、竞争格局和景气判断。</p>
        </div>
        <div class="source-card">
          <p class="section-tag">宏观指标</p>
          <h3>{{ store.payload?.macro?.length ?? 0 }}</h3>
          <p class="muted">国家统计局公开指标用来判断行业周期、需求环境和外部压力。</p>
        </div>
        <div class="source-card">
          <p class="section-tag">图表与表格</p>
          <h3>{{ qualitySummary ? `${(qualitySummary.multimodal_extract_coverage_ratio * 100).toFixed(0)}%` : '加载中' }}</h3>
          <p class="muted">复杂 PDF 里的表格和版面会被补成结构化证据，减少漏字段和读错表的问题。</p>
        </div>
      </div>
    </PagePanel>

    <PagePanel title="现在可以从这几家公司开始" eyebrow="Targets" description="系统先把常用分析对象准备好，避免你一进来不知道该点哪里。">
      <div class="target-spotlight-grid" v-if="store.payload?.targets?.length">
        <div v-for="item in store.payload.targets.slice(0, 6)" :key="item.company_code" class="target-spotlight-card">
          <div class="trace-title-row">
            <strong>{{ item.company_name }}</strong>
            <span class="badge-subtle">{{ item.exchange }}</span>
          </div>
          <p class="muted">{{ item.segment }} · {{ item.industry }}</p>
          <div class="button-row left-align">
            <button class="button-ghost" @click="openTarget(item.company_code, `${item.company_name}当前最值得关注的经营问题是什么？`)">直接提问</button>
            <RouterLink class="button-ghost" :to="`/workbench/${item.company_code}`">查看企业分析</RouterLink>
          </div>
        </div>
      </div>
    </PagePanel>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

import { api } from '../api/client';
import type { AgentResponse, QualitySummaryResponse } from '../api/types';
import PagePanel from '../components/PagePanel.vue';
import TracePanel from '../components/TracePanel.vue';
import { useDashboardStore } from '../stores/dashboard';

const router = useRouter();
const store = useDashboardStore();
const agentLoading = ref(false);
const agentResult = ref<AgentResponse | null>(null);
const qualitySummary = ref<QualitySummaryResponse | null>(null);
const selectedCode = ref('');
const question = ref('迈瑞医疗当前最值得关注的经营问题是什么？');

const quickPrompts = [
  '这家公司未来两年的主要风险和机会是什么？',
  '把这家公司的风险拆成财务、经营、行业三层',
  '如果我要继续跟踪它，接下来最该盯哪些指标？',
];

function currentCompanyName() {
  return store.targets.find((item) => item.company_code === selectedCode.value)?.company_name || '这家公司';
}

function normalizeQuestion(prompt: string) {
  return prompt.replace(/这家公司/g, currentCompanyName());
}

function applyPrompt(prompt: string) {
  question.value = normalizeQuestion(prompt);
  void runAgent();
}

function openTarget(companyCode: string, prompt: string) {
  selectedCode.value = companyCode;
  question.value = prompt;
  void runAgent();
  void router.push('/');
}

async function runAgent() {
  if (!question.value.trim()) return;
  agentLoading.value = true;
  try {
    agentResult.value = await api.queryAgent(question.value.trim());
  } finally {
    agentLoading.value = false;
  }
}

onMounted(async () => {
  if (!store.payload && !store.loading) {
    await store.load();
  }
  if (!selectedCode.value && store.targets.length) {
    selectedCode.value = store.targets[0].company_code;
    question.value = `${currentCompanyName()}当前最值得关注的经营问题是什么？`;
  }
  qualitySummary.value = await api.getQualitySummary();
  await runAgent();
});
</script>
