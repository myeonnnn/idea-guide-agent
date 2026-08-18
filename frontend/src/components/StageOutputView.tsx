import type {
  BusinessModelOutput,
  HypothesisOutput,
  HypothesisValidationOutput,
  MarketResearchOutput,
  MvpMlpOutput,
  StageName,
  StageOutputMap,
  TargetSegmentOutput,
} from "../types";
import { BulletList, ClaimList, Eyebrow, TagList } from "./Primitives";
import "./StageOutputView.css";

const ASSUMPTION_LABELS = {
  desirability: "고객이 원하는가",
  viability: "사업으로 성립하는가",
  feasibility: "만들 수 있는가",
};

const CONFIDENCE_LABELS = {
  low: "낮음",
  medium: "중간",
  high: "높음",
};

function MarketResearchView({ output }: { output: MarketResearchOutput }) {
  return (
    <>
      <p className="stage-summary">{output.summary}</p>
      <Eyebrow>시장 규모 근거</Eyebrow>
      <ClaimList claims={output.market_size_claims} />
      <Eyebrow>주요 경쟁자</Eyebrow>
      <TagList items={output.key_competitors} />
    </>
  );
}

function TargetSegmentView({ output }: { output: TargetSegmentOutput }) {
  return (
    <>
      <h3 className="stage-highlight">{output.primary_segment}</h3>
      <p className="stage-summary">{output.segment_description}</p>
      <Eyebrow>페인포인트</Eyebrow>
      <BulletList items={output.pain_points} />
      <Eyebrow>근거</Eyebrow>
      <ClaimList claims={output.claims} />
    </>
  );
}

function HypothesisView({ output }: { output: HypothesisOutput }) {
  return (
    <ul className="hypothesis-list">
      {output.hypotheses.map((h) => (
        <li key={h.statement} className="hypothesis-card">
          <span className={`assumption-tag assumption-${h.assumption_type}`}>
            {ASSUMPTION_LABELS[h.assumption_type]}
          </span>
          <p className="hypothesis-card__statement">{h.statement}</p>
          <p className="hypothesis-card__method">
            <span className="mono-label">검증 방법</span> {h.validation_method}
          </p>
        </li>
      ))}
    </ul>
  );
}

function HypothesisValidationView({ output }: { output: HypothesisValidationOutput }) {
  return (
    <ul className="hypothesis-list">
      {output.validations.map((v) => (
        <li key={v.hypothesis_statement} className="hypothesis-card">
          <span className={`confidence-tag confidence-${v.confidence}`}>
            확신도: {CONFIDENCE_LABELS[v.confidence]}
          </span>
          <p className="hypothesis-card__statement">{v.hypothesis_statement}</p>
          <p className="hypothesis-card__method">
            <span className="mono-label">검증 계획</span> {v.validation_plan}
          </p>
          <p className="hypothesis-card__method">
            <span className="mono-label">필요 증거</span> {v.required_evidence}
          </p>
        </li>
      ))}
    </ul>
  );
}

function MvpMlpView({ output }: { output: MvpMlpOutput }) {
  return (
    <>
      <Eyebrow>MVP 범위</Eyebrow>
      <BulletList items={output.mvp_scope} />
      <Eyebrow>MLP 범위</Eyebrow>
      <BulletList items={output.mlp_scope} />
      <Eyebrow>성공 지표</Eyebrow>
      <BulletList items={output.success_metrics} />
    </>
  );
}

function BusinessModelView({ output }: { output: BusinessModelOutput }) {
  return (
    <>
      <p className="stage-summary">{output.revenue_model}</p>
      <Eyebrow>채널</Eyebrow>
      <TagList items={output.channels} />
      <Eyebrow>비용 구조</Eyebrow>
      <BulletList items={output.cost_structure} />
      <Eyebrow>근거</Eyebrow>
      <ClaimList claims={output.claims} />
    </>
  );
}

interface StageOutputViewProps {
  stageName: StageName;
  output: StageOutputMap[StageName];
}

export function StageOutputView({ stageName, output }: StageOutputViewProps) {
  switch (stageName) {
    case "market_research":
      return <MarketResearchView output={output as MarketResearchOutput} />;
    case "target_segment":
      return <TargetSegmentView output={output as TargetSegmentOutput} />;
    case "hypothesis":
      return <HypothesisView output={output as HypothesisOutput} />;
    case "hypothesis_validation":
      return <HypothesisValidationView output={output as HypothesisValidationOutput} />;
    case "mvp_mlp":
      return <MvpMlpView output={output as MvpMlpOutput} />;
    case "business_model":
      return <BusinessModelView output={output as BusinessModelOutput} />;
  }
}
