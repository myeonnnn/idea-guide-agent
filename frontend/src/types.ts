export type SourceTier = "PRIMARY" | "SECONDARY" | "ESTIMATE";

export interface Claim {
  text: string;
  source_tier: SourceTier;
  source_url: string | null;
}

export interface MarketResearchOutput {
  summary: string;
  market_size_claims: Claim[];
  key_competitors: string[];
}

export interface TargetSegmentOutput {
  primary_segment: string;
  segment_description: string;
  pain_points: string[];
  claims: Claim[];
}

export type AssumptionType = "desirability" | "viability" | "feasibility";

export interface Hypothesis {
  statement: string;
  assumption_type: AssumptionType;
  validation_method: string;
}

export interface HypothesisOutput {
  hypotheses: Hypothesis[];
}

export type ConfidenceLevel = "low" | "medium" | "high";

export interface HypothesisValidationItem {
  hypothesis_statement: string;
  validation_plan: string;
  required_evidence: string;
  confidence: ConfidenceLevel;
}

export interface HypothesisValidationOutput {
  validations: HypothesisValidationItem[];
}

export interface MvpMlpOutput {
  mvp_scope: string[];
  mlp_scope: string[];
  success_metrics: string[];
}

export interface BusinessModelOutput {
  revenue_model: string;
  channels: string[];
  cost_structure: string[];
  claims: Claim[];
}

export const STAGE_NAMES = [
  "market_research",
  "target_segment",
  "hypothesis",
  "hypothesis_validation",
  "mvp_mlp",
  "business_model",
] as const;

export type StageName = (typeof STAGE_NAMES)[number];

export const STAGE_LABELS: Record<StageName, string> = {
  market_research: "시장조사",
  target_segment: "타겟층 설정",
  hypothesis: "가설 수립",
  hypothesis_validation: "가설 검증",
  mvp_mlp: "MVP / MLP 정의",
  business_model: "비즈니스모델 가정",
};

export type StageOutputMap = {
  market_research: MarketResearchOutput;
  target_segment: TargetSegmentOutput;
  hypothesis: HypothesisOutput;
  hypothesis_validation: HypothesisValidationOutput;
  mvp_mlp: MvpMlpOutput;
  business_model: BusinessModelOutput;
};

export interface CreateSessionResponse {
  session_id: string;
  stage_index: number;
}

export interface MessageResponseOk<S extends StageName = StageName> {
  status: "ok";
  stage_name: S;
  output: StageOutputMap[S];
  stage_index: number;
  complete: boolean;
}

export interface MessageResponseWarning {
  status: "warning";
  warning: string;
  raw_text: string;
  stage_index: number;
}

export type MessageResponse = MessageResponseOk | MessageResponseWarning;
