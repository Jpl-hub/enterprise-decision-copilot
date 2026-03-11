import type {
  AgentResponse,
  CompanyCompareResponse,
  CompanyReportResponse,
  CompetitionPackageResponse,
  DashboardPayload,
  DecisionBriefResponse,
  ManualReviewSubmitResponse,
  QualitySummaryResponse,
  RiskForecastResponse,
  RiskModelSummaryResponse,
  UniversePromotionPlanResponse,
  UniverseSummaryResponse,
  WarehouseOverviewResponse,
  WarehouseSummaryResponse,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE || '';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export const api = {
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
  queryAgent(question: string, options?: { threadId?: string | null; companyCode?: string | null; companyName?: string | null }) {
    return request<AgentResponse>('/api/agent/query', {
      method: 'POST',
      body: JSON.stringify({
        question,
        thread_id: options?.threadId || undefined,
        company_code: options?.companyCode || undefined,
        company_name: options?.companyName || undefined,
      }),
    });
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
