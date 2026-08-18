import type { SourceTier } from "../types";
import "./EvidenceBadge.css";

const TIER_META: Record<SourceTier, { mark: string; label: string; className: string }> = {
  PRIMARY: { mark: "●", label: "1차 출처", className: "tier-primary" },
  SECONDARY: { mark: "◐", label: "2차 해석", className: "tier-secondary" },
  ESTIMATE: { mark: "○", label: "AI 추정", className: "tier-estimate" },
};

interface EvidenceBadgeProps {
  tier: SourceTier;
  sourceUrl: string | null;
}

export function EvidenceBadge({ tier, sourceUrl }: EvidenceBadgeProps) {
  const meta = TIER_META[tier];
  const content = (
    <>
      <span className="evidence-badge__mark" aria-hidden="true">
        {meta.mark}
      </span>
      {meta.label}
    </>
  );

  if (sourceUrl) {
    return (
      <a
        className={`evidence-badge ${meta.className}`}
        href={sourceUrl}
        target="_blank"
        rel="noreferrer"
        title={sourceUrl}
      >
        {content}
      </a>
    );
  }

  return <span className={`evidence-badge ${meta.className}`}>{content}</span>;
}
