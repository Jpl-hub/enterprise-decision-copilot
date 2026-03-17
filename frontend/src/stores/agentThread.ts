import { defineStore } from 'pinia';

import { api } from '../api/client';
import type { AgentResponse, AgentThreadDetailResponse, AgentThreadMemory, AgentThreadMessage, AgentThreadSummary } from '../api/types';

interface AgentThreadState {
  threadId: string | null;
  threadTitle: string;
  threadSummary: string | null;
  threadMemory: AgentThreadMemory | null;
  focusCompanyCode: string | null;
  focusCompanyName: string | null;
  taskMode: string | null;
  loading: boolean;
  loadingHistory: boolean;
  error: string | null;
  latest: AgentResponse | null;
  messages: AgentThreadMessage[];
  history: AgentThreadSummary[];
}

export const useAgentThreadStore = defineStore('agent-thread', {
  state: (): AgentThreadState => ({
    threadId: null,
    threadTitle: '企业分析线程',
    threadSummary: null,
    threadMemory: null,
    focusCompanyCode: null,
    focusCompanyName: null,
    taskMode: null,
    loading: false,
    loadingHistory: false,
    error: null,
    latest: null,
    messages: [],
    history: [],
  }),
  actions: {
    setFocus(companyCode?: string | null, companyName?: string | null) {
      this.focusCompanyCode = companyCode != null ? String(companyCode) : null;
      this.focusCompanyName = companyName || null;
      if (companyName && (!this.threadTitle || this.threadTitle === '企业分析线程')) {
        this.threadTitle = companyName;
      }
    },
    setTaskMode(taskMode?: string | null) {
      this.taskMode = taskMode || null;
    },
    resetThread(companyCode?: string | null, companyName?: string | null) {
      this.threadId = null;
      this.threadTitle = companyName || '企业分析线程';
      this.threadSummary = null;
      this.threadMemory = null;
      this.focusCompanyCode = companyCode != null ? String(companyCode) : null;
      this.focusCompanyName = companyName || null;
      this.taskMode = null;
      this.latest = null;
      this.messages = [];
      this.error = null;
    },
    async ask(question: string, options?: { companyCode?: string | null; companyName?: string | null; taskMode?: string | null }) {
      this.loading = true;
      this.error = null;
      const previousMessages = [...this.messages];
      const now = new Date().toISOString();
      const liveStatus = options?.taskMode
        ? '正在检索证据并整理回答...'
        : '正在理解问题并整理回答...';
      this.messages = [
        ...this.messages,
        { role: 'user', content: question, created_at: now },
        { role: 'assistant', content: liveStatus, created_at: now },
      ];
      if (options?.companyCode || options?.companyName) {
        this.setFocus(options.companyCode, options.companyName);
      }
      if (options?.taskMode !== undefined) {
        this.setTaskMode(options.taskMode);
      }
      try {
        const explicitTaskMode = options?.taskMode !== undefined ? (options.taskMode || undefined) : undefined;
        const response = await api.queryAgent(question, {
          threadId: this.threadId,
          companyCode: options?.companyCode ?? this.focusCompanyCode,
          companyName: options?.companyName ?? this.focusCompanyName,
          taskMode: explicitTaskMode,
        });
        this.threadId = response.thread_id;
        this.threadTitle = response.thread_title;
        this.threadSummary = response.thread_summary || null;
        this.threadMemory = response.thread_memory || null;
        this.focusCompanyCode = response.focus?.company_code || this.focusCompanyCode;
        this.focusCompanyName = response.focus?.company_name || this.focusCompanyName;
        this.taskMode = response.task_mode || this.taskMode;
        this.latest = response;
        this.messages = response.thread_messages;
        void this.loadHistory();
        return response;
      } catch (error) {
        this.messages = previousMessages;
        this.error = error instanceof Error ? error.message : 'Agent 请求失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async loadHistory(limit = 20) {
      this.loadingHistory = true;
      try {
        const response = await api.getAgentThreads(limit);
        this.history = response.items;
        return response.items;
      } finally {
        this.loadingHistory = false;
      }
    },
    async openThread(threadId: string) {
      this.loading = true;
      this.error = null;
      try {
        const response: AgentThreadDetailResponse = await api.getAgentThread(threadId);
        this.threadId = response.thread_id;
        this.threadTitle = response.title;
        this.threadSummary = response.thread_summary || null;
        this.threadMemory = response.thread_memory || null;
        this.focusCompanyCode = response.focus?.company_code || null;
        this.focusCompanyName = response.focus?.company_name || null;
        this.taskMode = response.last_task_mode || null;
        this.messages = response.messages;
        this.latest = null;
        return response;
      } catch (error) {
        this.error = error instanceof Error ? error.message : '线程加载失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },
  },
});
