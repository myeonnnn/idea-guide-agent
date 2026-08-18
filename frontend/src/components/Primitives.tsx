import type { ReactNode } from "react";
import type { Claim } from "../types";
import { EvidenceBadge } from "./EvidenceBadge";
import "./Primitives.css";

export function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="eyebrow">{children}</div>;
}

export function TagList({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <ul className="tag-list">
      {items.map((item) => (
        <li key={item} className="tag-list__item">
          {item}
        </li>
      ))}
    </ul>
  );
}

export function BulletList({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <ul className="bullet-list">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export function ClaimList({ claims }: { claims: Claim[] }) {
  if (claims.length === 0) return null;
  return (
    <ul className="claim-list">
      {claims.map((claim) => (
        <li key={claim.text} className="claim-list__item">
          <p className="claim-list__text">{claim.text}</p>
          <EvidenceBadge tier={claim.source_tier} sourceUrl={claim.source_url} />
        </li>
      ))}
    </ul>
  );
}
