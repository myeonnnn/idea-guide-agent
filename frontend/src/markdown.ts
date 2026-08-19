import { STAGE_LABELS, type Claim, type MessageResponseOk, type StageOutputMap } from "./types";

const TIER_LABELS: Record<Claim["source_tier"], string> = {
  PRIMARY: "1차 출처",
  SECONDARY: "2차 해석",
  ESTIMATE: "AI 추정",
};

const ASSUMPTION_LABELS = {
  desirability: "고객이 원하는가",
  viability: "사업으로 성립하는가",
  feasibility: "만들 수 있는가",
};

const CONFIDENCE_LABELS = { low: "낮음", medium: "중간", high: "높음" };

function claimLine(claim: Claim): string {
  const tier = TIER_LABELS[claim.source_tier];
  const source = claim.source_url ? ` ([출처](${claim.source_url}))` : "";
  return `- ${claim.text} — *${tier}*${source}`;
}

function bulletBlock(items: string[]): string {
  return items.map((item) => `- ${item}`).join("\n");
}

function stageBody(result: MessageResponseOk): string {
  const { stage_name: name, output } = result;
  switch (name) {
    case "target_segment": {
      const o = output as StageOutputMap["target_segment"];
      return [
        `**${o.primary_segment}**`,
        "",
        o.segment_description,
        "",
        "**페인포인트**",
        bulletBlock(o.pain_points),
        "",
        "**근거**",
        o.claims.map(claimLine).join("\n"),
      ].join("\n");
    }
    case "market_research": {
      const o = output as StageOutputMap["market_research"];
      return [
        o.summary,
        "",
        "**시장 규모 근거**",
        o.market_size_claims.map(claimLine).join("\n"),
        "",
        "**주요 경쟁자**",
        bulletBlock(o.key_competitors),
      ].join("\n");
    }
    case "value_proposition": {
      const o = output as StageOutputMap["value_proposition"];
      return [
        o.statement,
        "",
        "**차별화 포인트**",
        bulletBlock(o.differentiators),
        "",
        "**진입장벽**",
        o.unfair_advantage,
        "",
        "**근거**",
        o.claims.map(claimLine).join("\n"),
      ].join("\n");
    }
    case "hypothesis": {
      const o = output as StageOutputMap["hypothesis"];
      return o.hypotheses
        .map(
          (h) =>
            `- **[${ASSUMPTION_LABELS[h.assumption_type]}]** ${h.statement}\n  검증 방법: ${h.validation_method}`
        )
        .join("\n");
    }
    case "hypothesis_validation": {
      const o = output as StageOutputMap["hypothesis_validation"];
      const sorted = [...o.validations].sort((a, b) => a.risk_rank - b.risk_rank);
      return [
        `**가장 먼저 검증해야 할 가정**: ${o.riskiest_assumption}`,
        o.riskiest_assumption_reasoning,
        "",
        ...sorted.map(
          (v) =>
            `- **[위험도 ${v.risk_rank}순위 · 확신도 ${CONFIDENCE_LABELS[v.confidence]}]** ${v.hypothesis_statement}\n  검증 계획: ${v.validation_plan}\n  필요 증거: ${v.required_evidence}`
        ),
      ].join("\n");
    }
    case "mvp_mlp": {
      const o = output as StageOutputMap["mvp_mlp"];
      return [
        "**MVP 범위**",
        bulletBlock(o.mvp_scope),
        "",
        "**MLP 범위**",
        bulletBlock(o.mlp_scope),
        "",
        "**성공 지표**",
        bulletBlock(o.success_metrics),
      ].join("\n");
    }
    case "business_model": {
      const o = output as StageOutputMap["business_model"];
      return [
        o.revenue_model,
        "",
        "**채널**",
        bulletBlock(o.channels),
        "",
        "**비용 구조**",
        bulletBlock(o.cost_structure),
        "",
        "**근거**",
        o.claims.map(claimLine).join("\n"),
      ].join("\n");
    }
    case "roadmap_summary": {
      const o = output as StageOutputMap["roadmap_summary"];
      return [
        o.summary,
        "",
        "**다음 액션**",
        bulletBlock(o.key_next_actions),
        "",
        "**아직 검증되지 않은 것**",
        bulletBlock(o.still_unverified),
        "",
        "**근거 품질 요약**",
        o.evidence_quality_summary,
      ].join("\n");
    }
  }
}

export function buildMarkdownReport(idea: string, results: MessageResponseOk[]): string {
  const date = new Date().toLocaleDateString("ko-KR");
  const sections = results.map(
    (result, index) =>
      `## ${String(index + 1).padStart(2, "0")}. ${STAGE_LABELS[result.stage_name]}\n\n${stageBody(result)}`
  );
  return [`# 아이디어 로드맵 초안`, "", `**아이디어**: ${idea}`, `**생성일**: ${date}`, "", ...sections].join(
    "\n\n"
  );
}

export function downloadMarkdown(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}
