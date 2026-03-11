import { createRouter, createWebHistory } from 'vue-router';

import CompareView from '../views/CompareView.vue';
import CompetitionView from '../views/CompetitionView.vue';
import OverviewView from '../views/OverviewView.vue';
import QualityCenterView from '../views/QualityCenterView.vue';
import WorkbenchView from '../views/WorkbenchView.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'overview', component: OverviewView },
    { path: '/compare', name: 'compare', component: CompareView },
    { path: '/workbench/:companyCode?', name: 'workbench', component: WorkbenchView, props: true },
    { path: '/quality', name: 'quality', component: QualityCenterView },
    { path: '/competition/:companyCode?', name: 'competition', component: CompetitionView, props: true },
  ],
});
