import { createRouter, createWebHistory } from 'vue-router';

import AuditView from '../views/AuditView.vue';
import CompareView from '../views/CompareView.vue';
import CompetitionView from '../views/CompetitionView.vue';
import LoginView from '../views/LoginView.vue';
import OverviewView from '../views/OverviewView.vue';
import QualityCenterView from '../views/QualityCenterView.vue';
import ThreadsView from '../views/ThreadsView.vue';
import WorkbenchView from '../views/WorkbenchView.vue';
import { getStoredAuthToken } from '../utils/auth';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'overview', component: OverviewView, meta: { requiresAuth: true } },
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

router.beforeEach((to) => {
  const hasToken = Boolean(getStoredAuthToken());
  if (to.name !== 'login' && to.meta.requiresAuth && !hasToken) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.name === 'login' && hasToken) {
    return { name: 'overview' };
  }
  return true;
});
