export type Relevance = "direct" | "indirect";

export interface SourceRecord {
  source_id: string;
  title: string;
  publisher: string;
  url: string;
  source_type: string;
  published_at: string | null;
  checked_at: string;
}

export interface ThemeDefinition {
  name: string;
  description: string;
  inclusion_criteria: string;
  exclusion_criteria: string;
}

export interface DomesticCandidate {
  name: string;
  code: string;
  exchange: string;
  security_type: string;
  related_business: string;
  relevance: Relevance;
  selection_reason: string;
  sources: SourceRecord[];
}

export interface DomesticMetrics {
  candidate_code: string;
  close_price: number | null;
  previous_day_price_change_percent: number | null;
  current_day_price_change_percent: number | null;
  weekly_price_change_percent: number | null;
  monthly_price_change_percent: number | null;
  market_cap: number | null;
  per: number | null;
  pbr: number | null;
  revenue_growth: number | null;
  operating_margin: number | null;
  market_data_as_of: string | null;
  financial_period: string | null;
  sources: SourceRecord[];
}

export interface PriceVolumeMetrics {
  candidate_code: string;
  analysis_period: string;
  period_return: number | null;
  volatility: number | null;
  volume_change: number | null;
  volume_surge: boolean | null;
  data_as_of: string | null;
}

export interface RiskItem {
  candidate_code: string;
  category: "company" | "disclosure_news" | "industry" | "check_point";
  fact: string;
}

export interface NewsDisclosureItem {
  candidate_code: string;
  category: "news" | "disclosure";
  title: string;
  summary: string;
  url: string;
  published_at: string | null;
  source: SourceRecord;
}

export interface USMarketReference {
  theme: string;
  trend: string;
  background: string;
  representative_companies: string[];
  representative_etfs: string[];
  news_summary: string;
  as_of: string | null;
  market_snapshots: USMarketSnapshot[];
  macro_indicators: USMacroIndicator[];
}

export interface USMarketSnapshot {
  ticker: string;
  name: string;
  instrument_type: string;
  close_price: number | null;
  daily_change_percent: number | null;
  volume: number | null;
  volume_change_percent: number | null;
  as_of: string | null;
}

export interface USMacroIndicator {
  label: string;
  ticker: string;
  snapshot: USMarketSnapshot;
  interpretation: string;
  domestic_check_point: string;
}

export interface USPeerCompany {
  name: string;
  ticker: string;
  related_business: string;
  connection: string;
  relevance: Relevance;
  market_snapshot: USMarketSnapshot | null;
  closing_news_summary: string;
  closing_news_url: string;
}

export interface AssetManagerReference {
  manager: string;
  market: "KR" | "GLOBAL";
  etf_or_holding: string;
  public_view: string;
  recent_activity: string;
  as_of: string | null;
  source_url: string;
}

export interface ResearchReport {
  request: { theme: string; top_n: number };
  generated_at: string;
  theme_definition: ThemeDefinition;
  candidates: DomesticCandidate[];
  metrics: DomesticMetrics[];
  price_volume_metrics: PriceVolumeMetrics[];
  risks: RiskItem[];
  news_disclosures: NewsDisclosureItem[];
  sources: SourceRecord[];
  disclaimer: string;
  us_market_reference: USMarketReference | null;
  us_peer_companies: USPeerCompany[];
  asset_manager_references: AssetManagerReference[];
}
