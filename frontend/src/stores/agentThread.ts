import { defineStore } from 'pinia';

import { api } from '../api/client';
import type { AgentResponse, AgentThreadDetailResponse, AgentThreadMessage, AgentThreadSummary } from '../api/types';

interface AgentThreadState {
  threadId: string | null;
  threadTitle: string;
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
      this.focusCompanyCode = companyCode || null;
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
      this.focusCompanyCode = companyCode || null;
      this.focusCompanyName = companyName || null;
      this.latest = null;
      this.messages = [];
      this.error = null;
    },
    async ask(question: string, options?: { companyCode?: string | null; companyName?: string | null; taskMode?: string | null }) {
      this.loading = true;
      this.error = null;
      if (options?.companyCode || options?.companyName) {
        this.setFocus(options.companyCode, options.companyName);
      }
      if (options?.taskMode !== undefined) {
        this.setTaskMode(options.taskMode);
      }
      try {
        const response = await api.queryAgent(question, {
          threadId: this.threadId,
          companyCode: options?.companyCode ?? this.focusCompanyCode,
          companyName: options?.companyName ?? this.focusCompanyName,
          taskMode: options?.taskMode ?? this.taskMode,
        });
        this.threadId = response.thread_id;
        this.threadTitle = response.thread_title;
        this.focusCompanyCode = response.focus?.company_code || this.focusCompanyCode;
        this.focusCompanyName = response.focus?.company_name || this.focusCompanyName;
        this.taskMode = response.task_mode || this.taskMode;
        this.latest = response;
        this.messages = response.thread_messages;
        return response;
      } catch (error) {
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
        this.focusCompanyCode = response.focus?.company_code || null;
        this.focusCompanyName = response.focus?.company_name || null;
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
