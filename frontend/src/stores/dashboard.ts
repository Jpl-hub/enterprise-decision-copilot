import { defineStore } from 'pinia';

import { api } from '../api/client';
import type { DashboardPayload } from '../api/types';

interface DashboardState {
  payload: DashboardPayload | null;
  loading: boolean;
  error: string | null;
}

export const useDashboardStore = defineStore('dashboard', {
  state: (): DashboardState => ({
    payload: null,
    loading: false,
    error: null,
  }),
  getters: {
    targets(state) {
      return state.payload?.targets || [];
    },
  },
  actions: {
    async load() {
      this.loading = true;
      this.error = null;
      try {
        this.payload = await api.getDashboard();
      } catch (error) {
        this.error = error instanceof Error ? error.message : '加载仪表盘失败';
      } finally {
        this.loading = false;
      }
    },
  },
});
