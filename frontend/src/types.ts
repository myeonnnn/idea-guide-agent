export type SourceTier = "PRIMARY" | "SECONDARY" | "ESTIMATE";

export interface Claim {
  text: string;
  source_tier: SourceTier;
  source_url: string | null;
}

export interface TargetSegmentOutput {
  primary_segment: string;
  segment_description: string;
  pain_points: string[];
  claims: Claim[];
}

export interface MarketResearchOutput {
  summary: string;
  market_size_claims: Claim[];
  key_competitors: string[];
}

export interface ValuePropositionOutput {
  statement: string;
  differentiators: string[];
  unfair_advantage: string;
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
  risk_rank: number;
}

export interface HypothesisValidationOutput {
  validations: HypothesisValidationItem[];
  riskiest_assumption: string;
  riskiest_assumption_reasoning: string;
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

export type VerdictType = "proceed" | "pivot" | "kill";

export interface FinalVerdictOutput {
  verdict: VerdictType;
  reasoning: string;
  key_unvalidated_assumptions: string[];
  evidence_quality_summary: string;
}

export const STAGE_NAMES = [
  "target_segment",
  "market_research",
  "value_proposition",
  "hypothesis",
  "hypothesis_validation",
  "mvp_mlp",
  "business_model",
  "final_verdict",
] as const;

export type StageName = (typeof STAGE_NAMES)[number];

export const STAGE_LABELS: Record<StageName, string> = {
  target_segment: "타겟층 설정",
  market_research: "시장조사",
  value_proposition: "가치제안 · 차별화",
  hypothesis: "가설 수립",
  hypothesis_validation: "가설 검증",
  mvp_mlp: "MVP / MLP 정의",
  business_model: "비즈니스모델 가정",
  final_verdict: "종합 판단",
};

export type StageOutputMap = {
  target_segment: TargetSegmentOutput;
  market_research: MarketResearchOutput;
  value_proposition: ValuePropositionOutput;
  hypothesis: HypothesisOutput;
  hypothesis_validation: HypothesisValidationOutput;
  mvp_mlp: MvpMlpOutput;
  business_model: BusinessModelOutput;
  final_verdict: FinalVerdictOutput;
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
