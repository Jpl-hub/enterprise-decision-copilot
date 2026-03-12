export interface AIHeadlineMetric {
  label: string;
  value: string;
  tone: string;
}

export interface AIEngineMetricSet {
  sample_count?: number | null;
  roc_auc?: number | null;
  model_type?: string | null;
  trained_at?: string | null;
  feature_count?: number | null;
  coverage_ratio?: number | null;
  avg_filled_field_count?: number | null;
  backends: string[];
  extract_report_count?: number | null;
  expected_report_count?: number | null;
  text_extract_report_count?: number | null;
  sft_sample_count?: number | null;
  artifact_count?: number | null;
  warehouse_table_count?: number | null;
  warehouse_row_count?: number | null;
  mart_view_count?: number | null;
  parquet_artifact_count?: number | null;
  tool_count?: number | null;
  official_coverage_ratio?: number | null;
  pending_review_count?: number | null;
  anomaly_company_count?: number | null;
}

export interface AIEngineSummary {
  engine_id: string;
  name: string;
  category: string;
  status: string;
  stage_label?: string | null;
  readiness_score?: number | null;
  role: string;
  primary_inputs: string[];
  primary_outputs: string[];
  headline_metrics: AIHeadlineMetric[];
  gaps: string[];
  metrics?: AIEngineMetricSet | null;
}

export interface AIPillarSummary {
  pillar_id: string;
  name: string;
  status: string;
  stage_label: string;
  readiness_score: number;
  summary: string;
  headline_metrics: AIHeadlineMetric[];
  strengths: string[];
  gaps: string[];
  next_steps: string[];
}

export interface AIStackSummaryResponse {
  generated_at: string;
  pillars: AIPillarSummary[];
  engines: AIEngineSummary[];
  priority_actions: string[];
  system_story: string[];
  design_choices: string[];
}

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

export interface AuditLogItem {
  log_id: string;
  user_id?: string | null;
  event_type: string;
  target_type?: string | null;
  target_id?: string | null;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogListResponse {
  total: number;
  items: AuditLogItem[];
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

export interface DashboardFreshnessPeriod {
  period_type: string;
  period_label: string;
  covered_companies: number;
  coverage_ratio: number;
  latest_report_year?: number | null;
  latest_published_at?: string | null;
  latest_company_name?: string | null;
}

export interface DashboardFreshness {
  annual_report_year?: number | null;
  annual_report_published_at?: string | null;
  latest_research_report?: string | null;
  latest_industry_report?: string | null;
  latest_macro_period?: string | null;
  latest_official_disclosure?: string | null;
  latest_periodic_label?: string | null;
  period_summaries: DashboardFreshnessPeriod[];
}

export interface DashboardPayload {
  status: PipelineStatus;
  targets: TargetCompany[];
  metrics: DashboardMetrics | null;
  freshness?: DashboardFreshness | null;
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

export interface MultimodalMetricItem {
  field: string;
  label: string;
  value?: number | null;
  display_value: string;
}

export interface MultimodalAssetLink {
  label: string;
  group?: string | null;
  url?: string | null;
}

export interface MultimodalEvidenceDigest {
  available: boolean;
  company_code?: string | null;
  company_name?: string | null;
  report_year?: number | null;
  published_at?: string | null;
  backend?: string | null;
  model_id?: string | null;
  source_url?: string | null;
  filled_field_count: number;
  field_source_count?: number | null;
  page_refs: string[];
  page_asset_links: MultimodalAssetLink[];
  notes: string[];
  metrics: MultimodalMetricItem[];
  summary: string;
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
  multimodal_field_count?: number | null;
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

export interface CompareCompanyFreshnessDigest {
  annual_report_year?: number | null;
  annual_report_published_at?: string | null;
  latest_official_disclosure?: string | null;
  latest_periodic_label?: string | null;
  latest_stock_report?: string | null;
  latest_industry_report?: string | null;
}

export interface CompareEvidenceDigest {
  count?: number;
  positive?: number;
  negative?: number;
  latest_titles?: string[];
  latest_institutions?: string[];
  latest_rows?: Array<Record<string, unknown>>;
  industries?: string[];
  start_year?: number;
  end_year?: number;
  revenue_cagr_pct?: number;
  profit_cagr_pct?: number;
}

export interface CompareEvidenceCompany {
  company_code: string;
  company_name: string;
  financial_source_url?: string | null;
  financial_published_at?: string | null;
  trend_digest?: CompareEvidenceDigest;
  research_digest?: CompareEvidenceDigest;
  industry_digest?: CompareEvidenceDigest;
  multimodal_digest?: MultimodalEvidenceDigest;
  risk_flags?: string[];
  freshness_digest?: CompareCompanyFreshnessDigest;
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
    companies?: CompareEvidenceCompany[];
    freshness?: CompareCompanyFreshnessDigest;
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

export interface AgentThreadMemory {
  task_label?: string | null;
  conclusion?: string | null;
  key_signals: string[];
  next_steps: string[];
  evidence_focus: string[];
}

export interface AgentThreadSummary {
  thread_id: string;
  title: string;
  focus?: AgentFocus | null;
  thread_summary?: string | null;
  thread_memory?: AgentThreadMemory | null;
  last_task_mode?: string | null;
  last_task_label?: string | null;
  last_message?: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface AgentThreadListResponse {
  total: number;
  items: AgentThreadSummary[];
}

export interface AgentThreadDetailResponse {
  thread_id: string;
  title: string;
  focus?: AgentFocus | null;
  thread_summary?: string | null;
  thread_memory?: AgentThreadMemory | null;
  last_task_mode?: string | null;
  last_task_label?: string | null;
  created_at: string;
  updated_at: string;
  messages: AgentThreadMessage[];
}

export interface AgentResponse {
  title: string;
  summary: string;
  highlights: string[];
  suggested_questions: string[];
  evidence?: Record<string, unknown> | null;
  trace: AgentTraceStep[];
  plan: AgentPlanStep[];
  task_mode: string;
  task_label: string;
  skill_id?: string | null;
  skill_label?: string | null;
  stage_label: string;
  deliverables: string[];
  thread_id: string;
  thread_title: string;
  focus?: AgentFocus | null;
  thread_summary?: string | null;
  thread_memory?: AgentThreadMemory | null;
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

export interface QualityIssueBreakdown {
  missing_reports: number;
  field_gaps: number;
  multimodal_missing: number;
  multimodal_low_coverage: number;
}

export interface QualitySummaryResponse {
  official_report_coverage_ratio: number;
  official_report_downloaded_slots: number;
  official_report_expected_slots: number;
  missing_report_slots: number;
  target_pool_company_count: number;
  target_pool_ready: boolean;
  universe_report_downloaded_slots: number;
  universe_report_expected_slots: number;
  universe_report_coverage_ratio: number;
  pending_review_count: number;
  anomaly_company_count: number;
  issue_breakdown: QualityIssueBreakdown;
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

export interface DataFoundationHotspotField {
  table: string;
  field: string;
  null_ratio: number;
}

export interface DataFoundationDatasetProfile {
  table: string;
  rows: number;
  columns: number;
  duplicate_rows: number;
  max_null_ratio: number;
  hotspot_fields: DataFoundationHotspotField[];
}

export interface DataFoundationLayerProfile {
  layer: string;
  table_count: number;
  row_count: number;
}

export interface DataFoundationSummaryResponse {
  warehouse_db?: string | null;
  warehouse_table_count: number;
  mart_views: string[];
  csv_artifact_count: number;
  parquet_artifact_count: number;
  total_warehouse_rows: number;
  lake_layers: DataFoundationLayerProfile[];
  dataset_profiles: DataFoundationDatasetProfile[];
  top_null_fields: DataFoundationHotspotField[];
  official_inventory_rows: number;
  multimodal_extract_report_count: number;
}

export interface PreparationSourceStatus {
  source_key: string;
  label: string;
  rows: number;
  latest?: string | null;
  coverage_note?: string | null;
}

export interface PreparationCandidate {
  company_code: string;
  company_name: string;
  industry_name?: string | null;
  report_count: number;
  institution_count: number;
  latest_report_date?: string | null;
  priority_score: number;
}

export interface PreparationPromotionExchangeStatus {
  exchange: string;
  selected_companies: number;
  downloaded_reports: number;
  missing_reports: number;
}

export interface PreparationPromotionCompany {
  company_code: string;
  company_name: string;
  exchange: string;
  industry_name?: string | null;
  priority_score: number;
  downloaded_reports: number;
  downloaded_years: number[];
  missing_years: number[];
  latest_published_at?: string | null;
}

export interface DataPreparationSummaryResponse {
  generated_at?: string | null;
  source_count: number;
  processed_dataset_count: number;
  target_pool_company_count: number;
  universe_company_count: number;
  annual_years: number[];
  latest_macro_period?: string | null;
  latest_stock_report_date?: string | null;
  latest_industry_report_date?: string | null;
  periodic_report_rows: number;
  promotion_candidate_count: number;
  selected_candidate_count: number;
  promotion_years: number[];
  promoted_report_download_count: number;
  promoted_report_missing_count: number;
  promoted_ready_company_count: number;
  promoted_partial_company_count: number;
  multimodal_sft_sample_count: number;
  multimodal_extract_count: number;
  risk_model_file_count: number;
  source_status: PreparationSourceStatus[];
  top_candidates: PreparationCandidate[];
  promoted_exchange_status: PreparationPromotionExchangeStatus[];
  promoted_companies: PreparationPromotionCompany[];
  preparation_notes: string[];
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
