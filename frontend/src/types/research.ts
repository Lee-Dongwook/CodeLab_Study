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
  related_business: string;
  relevance: Relevance;
  selection_reason: string;
}

export interface DomesticMetrics {
  candidate_code: string;
  close_price: number | null;
  market_cap: number | null;
  per: number | null;
  pbr: number | null;
  revenue_growth: number | null;
  operating_margin: number | null;
  market_data_as_of: string | null;
  financial_period: string | null;
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
}

export interface ResearchReport {
  generated_at: string;
  theme_definition: ThemeDefinition;
  candidates: DomesticCandidate[];
  metrics: DomesticMetrics[];
  price_volume_metrics: PriceVolumeMetrics[];
  risks: RiskItem[];
  news_disclosures: NewsDisclosureItem[];
  sources: SourceRecord[];
  disclaimer: string;
}
