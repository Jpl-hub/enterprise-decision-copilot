export interface PipelineStatus {
  has_financials: boolean;
  has_reports: boolean;
  has_macro: boolean;
}

export interface AuthUser {
  user_id: string;
  username: string;
  display_name: string;
  role: string;
  created_at: string;
  last_login_at?: string | null;
}

export interface LoginResponse {
  token: string;
  expires_at: string;
  user: AuthUser;
}

export interface RegisterResponse {
  user: AuthUser;
}

export interface TargetCompany {
  company_code: string;
  company_name: string;
  exchange: string;
  industry: string;
  segment: string;
}

export interface DashboardMetrics {
  sample_count: number;
  latest_year: number;
  avg_score: number;
  leader_name: string;
  leader_score: number;
  research_report_count: number;
  industry_report_count: number;
}

export interface DashboardPayload {
  status: PipelineStatus;
  targets: TargetCompany[];
  metrics: DashboardMetrics | null;
  ranking: Array<Record<string, unknown>>;
  watchlist: Array<Record<string, unknown>>;
  macro: Array<Record<string, unknown>>;
}

export interface EvidenceItem {
  title: string;
  source_url?: string | null;
  report_date?: string | null;
  institution?: string | null;
  industry_name?: string | null;
  matched_excerpt?: string | null;
  rerank_score?: number;
  ranking_signals?: string[];
}

export interface CompanyReportResponse {
  company_code: string;
  company_name: string;
  report_year: number;
  summary: string;
  sections: Array<{ title: string; content: string }>;
  strengths: string[];
  risks: string[];
  evidence: Record<string, unknown>;
}

export interface DecisionBriefResponse {
  company_code: string;
  company_name: string;
  question: string;
  verdict: string;
  summary: string;
  key_judgements: string[];
  action_recommendations: string[];
  evidence_highlights: string[];
  evidence: {
    query_terms?: string[];
    semantic_stock_reports?: EvidenceItem[];
    semantic_industry_reports?: EvidenceItem[];
    financial_source_url?: string;
  } & Record<string, unknown>;
}

export interface RiskModelSummaryResponse {
  model_ready: boolean;
  model_type?: string | null;
  trained_at?: string | null;
  sample_count: number;
  positive_samples: number;
  metrics: {
    accuracy?: number | null;
    precision?: number | null;
    recall?: number | null;
    f1?: number | null;
    roc_auc?: number | null;
    positive_rate?: number | null;
  };
  feature_columns: string[];
}

export interface RiskContributionItem {
  feature: string;
  contribution: number;
  direction: string;
}

export interface RiskModelPredictionResponse {
  company_code: string;
  report_year: number;
  high_risk_probability: number;
  predicted_score: number;
  top_contributions: RiskContributionItem[];
  model_summary: RiskModelSummaryResponse;
}

export interface RiskForecastResponse {
  company_code: string;
  company_name: string;
  risk_score: number;
  risk_level: string;
  summary: string;
  drivers: string[];
  monitoring_items: string[];
  heuristic_score: number;
  model_prediction?: RiskModelPredictionResponse | null;
  evidence: Record<string, unknown>;
}

export interface CompanyComparisonRow {
  company_code: string;
  company_name: string;
  total_score: number;
  risk_level: string;
  revenue_million: number;
  net_profit_million: number;
  net_margin_pct?: number | null;
  roe_pct?: number | null;
  rd_ratio_pct?: number | null;
  revenue_cagr_pct?: number | null;
  profit_cagr_pct?: number | null;
  research_report_count: number;
  industry_report_count: number;
}

export interface ComparisonDimensionValue {
  company_code: string;
  company_name: string;
  value: number;
}

export interface ComparisonDimension {
  dimension: string;
  winner_company_code: string;
  winner_company_name: string;
  conclusion: string;
  values: ComparisonDimensionValue[];
}

export interface CompanyCompareResponse {
  report_year: number;
  winner_company_code: string;
  winner_company_name: string;
  summary: string;
  highlights: string[];
  comparison_rows: CompanyComparisonRow[];
  dimensions: ComparisonDimension[];
  evidence: {
    companies?: Array<{
      company_code: string;
      company_name: string;
      financial_source_url?: string | null;
      trend_digest?: Record<string, unknown>;
      research_digest?: Record<string, unknown>;
      industry_digest?: Record<string, unknown>;
      risk_flags?: string[];
    }>;
  } & Record<string, unknown>;
}

export interface UniverseExchangeItem {
  exchange: string;
  company_count: number;
  report_count: number;
}

export interface UniverseIndustryItem {
  industry_code?: string | null;
  industry_name: string;
  company_count: number;
  report_count: number;
}

export interface UniverseCompanyItem {
  company_code: string;
  company_name: string;
  exchange: string;
  market?: string | null;
  industry_code?: string | null;
  industry_name: string;
  report_count: number;
  institution_count: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  latest_report_date?: string | null;
  earliest_report_date?: string | null;
  in_target_pool: boolean;
  latest_report_title?: string | null;
  latest_source_url?: string | null;
}

export interface UniverseCandidateRecommendationItem extends UniverseCompanyItem {
  candidate_priority_score: number;
  recommendation_reasons: string[];
}

export interface UniversePromotionIndustryItem {
  industry_name: string;
  selected_count: number;
}

export interface UniverseFinancialReadinessItem {
  company_code: string;
  company_name: string;
  exchange: string;
  industry_name: string;
  candidate_priority_score: number;
  feature_year_count: number;
  report_years: string[];
  latest_report_year?: number | null;
  readiness_status: string;
  year_coverage_ratio: number;
}

export interface UniverseFinancialReadinessSummary {
  promotion_candidate_count: number;
  official_feature_company_count: number;
  official_feature_row_count: number;
  ready_candidate_count: number;
  partial_candidate_count: number;
  pending_candidate_count: number;
  average_year_coverage_ratio: number;
  candidates: UniverseFinancialReadinessItem[];
}

export interface UniversePromotionPlanResponse {
  plan_ready: boolean;
  generated_at?: string | null;
  limit: number;
  per_industry_limit: number;
  candidate_count: number;
  selected_count: number;
  industries: UniversePromotionIndustryItem[];
  candidates: UniverseCandidateRecommendationItem[];
}

export interface UniverseSummaryResponse {
  universe_ready: boolean;
  generated_at?: string | null;
  company_count: number;
  industry_count: number;
  total_report_count: number;
  target_overlap_count: number;
  exchanges: UniverseExchangeItem[];
  industries: UniverseIndustryItem[];
  top_companies: UniverseCompanyItem[];
  recommended_candidates: UniverseCandidateRecommendationItem[];
  industry_code_map: Record<string, string>;
  financial_readiness: UniverseFinancialReadinessSummary;
}

export interface AgentTraceStep {
  step: string;
  status: string;
  detail: string;
}

export interface AgentPlanStep {
  step: string;
  status: string;
  detail: string;
}

export interface AgentThreadMessage {
  role: string;
  content: string;
  created_at: string;
}

export interface AgentFocus {
  company_code?: string | null;
  company_name?: string | null;
}

export interface AgentResponse {
  title: string;
  summary: string;
  highlights: string[];
  suggested_questions: string[];
  evidence?: Record<string, unknown> | null;
  trace: AgentTraceStep[];
  plan: AgentPlanStep[];
  thread_id: string;
  thread_title: string;
  focus?: AgentFocus | null;
  thread_messages: AgentThreadMessage[];
}

export interface QualityAnomalyItem {
  company_code: string;
  company_name: string;
  report_year: number;
  field_coverage_ratio: number;
  critical_fields_missing: string[];
  anomaly_flags: string[];
  anomaly_score: number;
  exchange?: string | null;
  financial_source_url?: string | null;
}

export interface ExchangeQualityStatus {
  exchange: string;
  manifest_exists: boolean;
  rows: number;
  downloaded_rows: number;
  file_missing_rows: number;
  companies: string[];
}

export interface ManualReviewRecord {
  company_code: string;
  report_year: number;
  finding_level: string;
  finding_type: string;
  note: string;
  status: string;
  created_at: string;
}

export interface MultimodalExtractItem {
  company_code: string;
  report_year: number;
  company_name?: string | null;
  backend: string;
  model_id?: string | null;
  source_url?: string | null;
  page_images: string[];
  field_source_count: number;
  filled_field_count: number;
  notes: string[];
}

export interface QualitySummaryResponse {
  official_report_coverage_ratio: number;
  official_report_downloaded_slots: number;
  official_report_expected_slots: number;
  missing_report_slots: number;
  pending_review_count: number;
  anomaly_company_count: number;
  multimodal_extract_report_count: number;
  multimodal_expected_report_count: number;
  multimodal_extract_coverage_ratio: number;
  multimodal_avg_filled_field_count: number;
  multimodal_backends: string[];
  multimodal_recent_extracts: MultimodalExtractItem[];
  exchange_status: ExchangeQualityStatus[];
  top_anomalies: QualityAnomalyItem[];
  recent_reviews: ManualReviewRecord[];
}

export interface ManualReviewSubmitResponse {
  review: ManualReviewRecord;
  summary: QualitySummaryResponse;
}

export interface CompetitionPackageResponse {
  company_code: string;
  company_name: string;
  report_year: number;
  question: string;
  exported_at: string;
  summary: string;
  citation_count: number;
  export_dir?: string | null;
  markdown_path?: string | null;
  evidence_path?: string | null;
  sections: Array<{ title: string; content: string }>;
  citations: Array<{
    citation_id: string;
    source_type: string;
    title: string;
    source_url?: string | null;
    report_date?: string | null;
    institution?: string | null;
    excerpt?: string | null;
  }>;
  quality_snapshot: Record<string, unknown>;
  markdown_content: string;
}

export interface WarehouseSummaryResponse {
  warehouse_ready: boolean;
  warehouse_db?: string | null;
  table_count: number;
  latest_company_rows: number;
  mart_views: string[];
  tables: Array<{ schema_name: string; table: string; rows: number; parquet_path: string }>;
}

export interface WarehouseOverviewResponse extends WarehouseSummaryResponse {
  company_overview: Array<{
    company_code: string;
    company_name: string;
    report_year: number;
    revenue_million?: number | null;
    net_profit_million?: number | null;
    positive_reports: number;
    neutral_reports: number;
    negative_reports: number;
    report_coverage: number;
    published_at?: string | null;
  }>;
  industry_heat: Array<{
    industry_name: string;
    report_count: number;
    positive_count: number;
    negative_count: number;
    latest_report_date?: string | null;
  }>;
  company_research_heat: Array<{
    company_code: string;
    company_name: string;
    report_count: number;
    positive_count: number;
    negative_count: number;
    latest_report_date?: string | null;
  }>;
}
