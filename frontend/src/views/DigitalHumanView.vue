<template>
  <div class="page-stack digital-human-page">
    <section class="human-hero">
      <div>
        <span class="human-kicker">Digital Human Studio</span>
        <h1>数字人预留页</h1>
        <p>这里先只保留数字人模块的入口和场景位，不再继续做半成品聊天。等主问答稳定后，再把实时语音、视频和数字形象单独接进来。</p>
      </div>
      <div class="human-hero-actions">
        <button class="button-ghost" @click="resetChat">回到默认场景</button>
        <RouterLink to="/" class="button-primary">回到问答中枢</RouterLink>
      </div>
    </section>

    <section class="human-stage-shell">
      <div class="human-stage-panel">
        <div class="human-stage-copy">
          <span class="human-stage-label">{{ activeScene.label }}</span>
          <strong>{{ activeScene.host }}</strong>
          <p>{{ activeScene.summary }}</p>
        </div>
        <div class="human-avatar-stage">
          <div class="human-avatar-ring"></div>
          <div class="human-avatar-core">{{ activeScene.avatar }}</div>
          <div class="human-wave wave-a"></div>
          <div class="human-wave wave-b"></div>
        </div>
      </div>

      <aside class="human-scene-rail">
        <div class="human-scene-head">
          <span>场景切换</span>
          <strong>{{ scenes.length }} 个</strong>
        </div>
        <div class="human-scene-list">
          <button
            v-for="item in scenes"
            :key="item.id"
            class="human-scene-card"
            :class="{ active: sceneId === item.id }"
            @click="selectScene(item.id)"
          >
            <strong>{{ item.label }}</strong>
            <p>{{ item.summary }}</p>
          </button>
        </div>
      </aside>
    </section>

    <section class="human-chat-shell">
      <div class="human-chat-head">
        <div>
          <span>模块状态</span>
          <strong>数字人先保留入口，后续再单独深化</strong>
        </div>
        <div class="human-chat-chips">
          <span v-for="item in activeScene.tags" :key="item">{{ item }}</span>
        </div>
      </div>

      <div class="human-placeholder-grid">
        <article class="human-placeholder-card">
          <span>当前决定</span>
          <strong>先不继续做聊天交互</strong>
          <p>数字人页面当前只保留场景入口和展示位，不再继续和企业问答争抢交互优先级。</p>
        </article>
        <article class="human-placeholder-card">
          <span>后续扩展</span>
          <strong>语音 / 视频 / WebSocket</strong>
          <p>等企业问答、证据链和报告链稳定后，再单独推进实时会话、数字形象和娱乐化互动。</p>
        </article>
        <article class="human-placeholder-card">
          <span>当前预留场景</span>
          <strong>{{ activeScene.label }}</strong>
          <p>{{ activeScene.summary }}</p>
        </article>
      </div>

      <div class="human-prompt-row">
        <button v-for="item in activeScene.prompts" :key="item" class="human-prompt-chip" type="button">
          {{ item }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { RouterLink } from 'vue-router';

interface HumanScene {
  id: string;
  label: string;
  host: string;
  avatar: string;
  summary: string;
  prompts: string[];
  tags: string[];
}

const scenes: HumanScene[] = [
  {
    id: 'briefing',
    label: '投研陪聊',
    host: '数智助理',
    avatar: '智',
    summary: '适合轻量追问、观点陪跑和问题拆解，偏专业但不压迫。',
    prompts: ['用轻松点的方式解释一下企业经营风险', '把这家公司最近的亮点讲得像路演串词', '先别严肃分析，陪我理一下这家公司的重点'],
    tags: ['专业', '轻量', '陪跑'],
  },
  {
    id: 'rehearsal',
    label: '路演彩排',
    host: '答辩搭子',
    avatar: '演',
    summary: '适合口语化问答、答辩预演和表达润色。',
    prompts: ['你当评委来问我三个刁钻问题', '把这段结论改得更像答辩现场表达', '帮我模拟一个路演问答场景'],
    tags: ['答辩', '彩排', '表达'],
  },
  {
    id: 'fun',
    label: '轻松闲聊',
    host: '娱乐陪聊体',
    avatar: '聊',
    summary: '预留娱乐化和人格化聊天场景，后续接更鲜活的数字人设定。',
    prompts: ['如果这家公司是个角色，它会是什么性格', '用吐槽但不低级的方式讲讲这个行业', '给我来一个轻松一点的互动话题'],
    tags: ['轻松', '娱乐', '人格化'],
  },
];

const sceneId = ref<HumanScene['id']>('briefing');
const activeScene = computed(() => scenes.find((item) => item.id === sceneId.value) || scenes[0]);

function selectScene(id: HumanScene['id']) {
  sceneId.value = id;
}

function resetChat() {
  sceneId.value = 'briefing';
}
</script>

<style scoped>
.digital-human-page,
.human-hero,
.human-hero-actions,
.human-stage-shell,
.human-stage-panel,
.human-scene-rail,
.human-scene-list,
.human-chat-shell,
.human-prompt-row,
.human-chat-chips,
.human-placeholder-grid {
  display: grid;
  gap: 18px;
}

.human-hero,
.human-stage-shell,
.human-chat-shell {
  padding: 22px;
  border-radius: 32px;
  border: 1px solid rgba(10, 31, 68, 0.08);
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.08);
}

.human-hero {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  background:
    radial-gradient(circle at top left, rgba(52, 211, 153, 0.14), transparent 24%),
    linear-gradient(180deg, #fffef8, #f5f8fc);
}

.human-kicker,
.human-stage-label,
.human-chat-head span,
.human-scene-head span {
  display: inline-flex;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 700;
  color: #6c7e95;
}

.human-hero h1 {
  margin: 8px 0 10px;
  font-size: 42px;
}

.human-hero p {
  margin: 0;
  max-width: 760px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.human-hero-actions {
  grid-auto-flow: column;
}

.human-stage-shell {
  grid-template-columns: minmax(0, 1.28fr) minmax(280px, 0.72fr);
  background: linear-gradient(135deg, #0f1d34, #173255 55%, #264a72);
  color: #fff;
}

.human-stage-panel {
  align-content: center;
  justify-items: center;
  min-height: 360px;
}

.human-stage-copy {
  max-width: 560px;
  text-align: center;
}

.human-stage-copy strong {
  display: block;
  margin: 8px 0 10px;
  font-size: 34px;
}

.human-stage-copy p {
  margin: 0;
  line-height: 1.7;
  color: rgba(227, 236, 246, 0.82);
}

.human-avatar-stage {
  position: relative;
  display: grid;
  place-items: center;
  width: 260px;
  height: 260px;
  margin-top: 28px;
}

.human-avatar-ring,
.human-wave,
.human-avatar-core {
  position: absolute;
  border-radius: 50%;
}

.human-avatar-ring {
  inset: 26px;
  border: 1px solid rgba(255, 255, 255, 0.14);
}

.human-avatar-core {
  display: grid;
  place-items: center;
  width: 148px;
  height: 148px;
  background: radial-gradient(circle at 30% 30%, #84dfff, #3a84ff 56%, #102b59);
  color: #fff;
  font-size: 48px;
  font-weight: 800;
  box-shadow: 0 0 0 18px rgba(142, 187, 255, 0.08);
}

.human-wave {
  inset: 8px;
  border: 1px solid rgba(163, 201, 255, 0.18);
}

.wave-a {
  animation: pulse-a 2.4s ease-in-out infinite;
}

.wave-b {
  inset: 0;
  animation: pulse-b 2.4s ease-in-out infinite;
}

.human-scene-rail {
  align-content: start;
  padding: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.08);
}

.human-scene-head,
.human-chat-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.human-scene-head strong,
.human-chat-head strong {
  display: block;
  color: inherit;
}

.human-scene-list {
  grid-template-columns: 1fr;
}

.human-scene-card,
.human-prompt-chip {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  text-align: left;
  cursor: pointer;
}

.human-scene-card {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.human-scene-card.active {
  background: rgba(84, 160, 255, 0.24);
}

.human-scene-card p {
  margin: 8px 0 0;
  color: rgba(227, 236, 246, 0.82);
  line-height: 1.55;
}

.human-chat-shell {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 249, 252, 0.98));
}

.human-chat-chips {
  grid-auto-flow: column;
}

.human-chat-chips span {
  padding: 8px 12px;
  border-radius: 999px;
  background: #ecf4fb;
  color: #32557d;
  font-size: 12px;
  font-weight: 600;
}

.human-placeholder-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.human-placeholder-card {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(10, 31, 68, 0.08);
  background: rgba(248, 250, 252, 0.92);
}

.human-placeholder-card span {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 700;
  color: #6c7e95;
}

.human-placeholder-card strong {
  font-size: 22px;
  line-height: 1.2;
}

.human-placeholder-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.human-prompt-row {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.human-prompt-chip {
  background: #f8fbfd;
  border: 1px solid rgba(10, 31, 68, 0.08);
}

@keyframes pulse-a {
  0%, 100% { transform: scale(0.95); opacity: 0.5; }
  50% { transform: scale(1.02); opacity: 0.9; }
}

@keyframes pulse-b {
  0%, 100% { transform: scale(1.02); opacity: 0.28; }
  50% { transform: scale(1.12); opacity: 0.58; }
}

@media (max-width: 1180px) {
  .human-hero,
  .human-stage-shell {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .human-hero-actions,
  .human-chat-chips {
    grid-auto-flow: row;
    grid-template-columns: 1fr;
  }

  .human-scene-head,
  .human-chat-head {
    flex-direction: column;
    align-items: start;
  }

  .human-placeholder-grid {
    grid-template-columns: 1fr;
  }
}
</style>
