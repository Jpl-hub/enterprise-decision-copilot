import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

import AuditView from '../views/AuditView.vue';
import BoardView from '../views/BoardView.vue';
import CompareView from '../views/CompareView.vue';
import CompetitionView from '../views/CompetitionView.vue';
import LoginView from '../views/LoginView.vue';
import MissionControlView from '../views/MissionControlView.vue';
import OverviewView from '../views/OverviewView.vue';
import QualityCenterView from '../views/QualityCenterView.vue';
import ThreadsView from '../views/ThreadsView.vue';
import WorkbenchView from '../views/WorkbenchView.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'overview', component: OverviewView, meta: { requiresAuth: true } },
    { path: '/mission-control', name: 'mission-control', component: MissionControlView, meta: { requiresAuth: true } },
    { path: '/board', name: 'board', component: BoardView, meta: { requiresAuth: true } },
    { path: '/compare', name: 'compare', component: CompareView, meta: { requiresAuth: true } },
    { path: '/workbench/:companyCode?', name: 'workbench', component: WorkbenchView, props: true, meta: { requiresAuth: true } },
    { path: '/quality', name: 'quality', component: QualityCenterView, meta: { requiresAuth: true } },
    { path: '/threads', name: 'threads', component: ThreadsView, meta: { requiresAuth: true } },
    { path: '/audit', name: 'audit', component: AuditView, meta: { requiresAuth: true } },
    { path: '/competition/:companyCode?', name: 'competition', component: CompetitionView, props: true, meta: { requiresAuth: true } },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  if (!authStore.ready) {
    await authStore.restoreSession();
  }

  if (to.name !== 'login' && to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.name === 'login' && authStore.isAuthenticated) {
    return { name: 'overview' };
  }
  return true;
});
