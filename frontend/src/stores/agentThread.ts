import { defineStore } from 'pinia';

import { api } from '../api/client';
import type { AgentResponse, AgentThreadMessage } from '../api/types';

interface AgentThreadState {
  threadId: string | null;
  threadTitle: string;
  focusCompanyCode: string | null;
  focusCompanyName: string | null;
  loading: boolean;
  error: string | null;
  latest: AgentResponse | null;
  messages: AgentThreadMessage[];
}

export const useAgentThreadStore = defineStore('agent-thread', {
  state: (): AgentThreadState => ({
    threadId: null,
    threadTitle: '企业分析线程',
    focusCompanyCode: null,
    focusCompanyName: null,
    loading: false,
    error: null,
    latest: null,
    messages: [],
  }),
  actions: {
    setFocus(companyCode?: string | null, companyName?: string | null) {
      this.focusCompanyCode = companyCode || null;
      this.focusCompanyName = companyName || null;
      if (companyName && (!this.threadTitle || this.threadTitle === '企业分析线程')) {
        this.threadTitle = companyName;
      }
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
    async ask(question: string, options?: { companyCode?: string | null; companyName?: string | null }) {
      this.loading = true;
      this.error = null;
      if (options?.companyCode || options?.companyName) {
        this.setFocus(options.companyCode, options.companyName);
      }
      try {
        const response = await api.queryAgent(question, {
          threadId: this.threadId,
          companyCode: options?.companyCode ?? this.focusCompanyCode,
          companyName: options?.companyName ?? this.focusCompanyName,
        });
        this.threadId = response.thread_id;
        this.threadTitle = response.thread_title;
        this.focusCompanyCode = response.focus?.company_code || this.focusCompanyCode;
        this.focusCompanyName = response.focus?.company_name || this.focusCompanyName;
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
  },
});
