import { defineStore } from 'pinia';

import { api } from '../api/client';
import type { AuthUser } from '../api/types';
import { clearStoredAuthToken, getStoredAuthToken, setStoredAuthToken } from '../utils/auth';

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
      return Boolean(state.user && getStoredAuthToken());
    },
  },
  actions: {
    async restoreSession() {
      if (this.ready) return;
      const token = getStoredAuthToken();
      if (!token) {
        this.ready = true;
        return;
      }
      this.loading = true;
      try {
        this.user = await api.getMe();
      } catch (error) {
        clearStoredAuthToken();
        this.user = null;
        this.error = error instanceof Error ? error.message : '登录状态恢复失败';
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
        setStoredAuthToken(payload.token);
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
        if (getStoredAuthToken()) {
          await api.logout();
        }
      } finally {
        clearStoredAuthToken();
        this.user = null;
        this.ready = true;
      }
    },
  },
});
