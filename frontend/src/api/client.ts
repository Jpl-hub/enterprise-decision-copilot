import type {
  AIStackSummaryResponse,
  AgentResponse,
  AgentThreadDetailResponse,
  AgentThreadListResponse,
  AuditLogListResponse,
  AuthUser,
  CompanyCompareResponse,
  CompanyReportResponse,
  CompetitionPackageResponse,
  DashboardPayload,
  DecisionBriefResponse,
  LoginResponse,
  ManualReviewSubmitResponse,
  QualitySummaryResponse,
  RegisterResponse,
  RiskForecastResponse,
  RiskModelSummaryResponse,
  UniversePromotionPlanResponse,
  UniverseSummaryResponse,
  WarehouseOverviewResponse,
  WarehouseSummaryResponse,
} from './types';
import { clearStoredAuthToken, getStoredAuthToken } from '../utils/auth';

const API_BASE = import.meta.env.VITE_API_BASE || '';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredAuthToken();
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
    ...init,
  });

  if (response.status === 401) {
    clearStoredAuthToken();
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export const api = {
  register(username: string, displayName: string, password: string) {
    return request<RegisterResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, display_name: displayName, password }),
    });
  },
  login(username: string, password: string) {
    return request<LoginResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  },
  getMe() {
    return request<AuthUser>('/api/auth/me');
  },
  logout() {
    return request<{ success: boolean }>('/api/auth/logout', {
      method: 'POST',
    });
  },
  getAIStack() {
    return request<AIStackSummaryResponse>('/api/ai/stack');
  },
  getAuditLogs(limit = 30) {
    return request<AuditLogListResponse>(`/api/audit/logs?limit=${limit}`);
  },
  getDashboard() {
    return request<DashboardPayload>('/api/dashboard');
  },
  getCompanyReport(companyCode: string) {
    return request<CompanyReportResponse>(`/api/company/${companyCode}/report`);
  },
  getCompanyCompare(companyCodes: string[]) {
    const query = companyCodes.map((code) => `company_codes=${encodeURIComponent(code)}`).join('&');
    return request<CompanyCompareResponse>(`/api/company/compare?${query}`);
  },
  getDecisionBrief(companyCode: string, question: string) {
    const query = encodeURIComponent(question);
    return request<DecisionBriefResponse>(`/api/company/${companyCode}/decision-brief?question=${query}`);
  },
  getRiskForecast(companyCode: string) {
    return request<RiskForecastResponse>(`/api/company/${companyCode}/risk-forecast`);
  },
  getRiskModelSummary() {
    return request<RiskModelSummaryResponse>('/api/risk/model-summary');
  },
  getUniverseSummary() {
    return request<UniverseSummaryResponse>('/api/universe/summary');
  },
  getUniversePromotionPlan(limit = 12, perIndustry = 2) {
    return request<UniversePromotionPlanResponse>(`/api/universe/promotion-plan?limit=${limit}&per_industry=${perIndustry}`);
  },
  queryAgent(question: string, options?: { threadId?: string | null; companyCode?: string | null; companyName?: string | null; taskMode?: string | null }) {
    return request<AgentResponse>('/api/agent/query', {
      method: 'POST',
      body: JSON.stringify({
        question,
        thread_id: options?.threadId || undefined,
        company_code: options?.companyCode || undefined,
        company_name: options?.companyName || undefined,
        task_mode: options?.taskMode || undefined,
      }),
    });
  },
  getAgentThreads(limit = 20) {
    return request<AgentThreadListResponse>(`/api/agent/threads?limit=${limit}`);
  },
  getAgentThread(threadId: string) {
    return request<AgentThreadDetailResponse>(`/api/agent/threads/${threadId}`);
  },
  getQualitySummary() {
    return request<QualitySummaryResponse>('/api/quality/summary');
  },
  syncAutoReviews(limit = 12) {
    return request<{ created_count: number; skipped_count: number; created: Array<Record<string, unknown>>; summary: QualitySummaryResponse }>(`/api/quality/reviews/auto?limit=${limit}`, {
      method: 'POST',
    });
  },
  getWarehouseSummary() {
    return request<WarehouseSummaryResponse>('/api/warehouse/summary');
  },
  getWarehouseOverview(limit = 8) {
    return request<WarehouseOverviewResponse>(`/api/warehouse/overview?limit=${limit}`);
  },
  submitReview(payload: Record<string, unknown>) {
    return request<ManualReviewSubmitResponse>('/api/quality/reviews', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  getCompetitionPackage(companyCode: string, question: string, persist = true) {
    const query = encodeURIComponent(question);
    return request<CompetitionPackageResponse>(
      `/api/company/${companyCode}/competition-package?question=${query}&persist=${persist}`,
    );
  },
};
