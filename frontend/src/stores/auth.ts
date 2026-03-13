import { defineStore } from 'pinia';

import { api } from '../api/client';
import type { AuthUser } from '../api/types';

interface AuthState {
  user: AuthUser | null;
  loading: boolean;
  ready: boolean;
  error: string | null;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    loading: false,
    ready: false,
    error: null,
  }),
  getters: {
    isAuthenticated(state) {
      return Boolean(state.user);
    },
    role(state) {
      return state.user?.role || 'viewer';
    },
    canExport(state) {
      return ['admin', 'analyst'].includes(state.user?.role || '');
    },
    canManageReviews(state) {
      return ['admin', 'analyst'].includes(state.user?.role || '');
    },
    canAutoSyncReviews(state) {
      return (state.user?.role || '') === 'admin';
    },
    canViewAudit(state) {
      return (state.user?.role || '') === 'admin';
    },
  },
  actions: {
    async restoreSession() {
      if (this.ready) return;
      this.loading = true;
      this.error = null;
      try {
        this.user = await api.getMe();
      } catch (error) {
        this.user = null;
        const message = error instanceof Error ? error.message : '登录状态恢复失败';
        if (message !== '登录状态已失效，请重新登录。' && message !== '请先登录。') {
          this.error = message;
        }
      } finally {
        this.loading = false;
        this.ready = true;
      }
    },
    async login(username: string, password: string) {
      this.loading = true;
      this.error = null;
      try {
        const payload = await api.login(username, password);
        this.user = payload.user;
        this.ready = true;
      } catch (error) {
        this.error = error instanceof Error ? error.message : '登录失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async register(username: string, displayName: string, password: string) {
      this.loading = true;
      this.error = null;
      try {
        await api.register(username, displayName, password);
        await this.login(username, password);
      } finally {
        this.loading = false;
      }
    },
    async logout() {
      try {
        await api.logout();
      } finally {
        this.user = null;
        this.ready = true;
      }
    },
  },
});
