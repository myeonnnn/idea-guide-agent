import { STAGE_LABELS, STAGE_NAMES, type StageName } from "../types";
import "./SidebarNav.css";

interface SidebarNavProps {
  idea: string;
  currentIndex: number;
  onSelect: (name: StageName) => void;
}

export function SidebarNav({ idea, currentIndex, onSelect }: SidebarNavProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar__idea">
        <p className="mono-label">아이디어</p>
        <p className="sidebar__idea-text">{idea}</p>
      </div>
      <nav className="sidebar__nav">
        {STAGE_NAMES.map((name, index) => {
          const state =
            index < currentIndex ? "done" : index === currentIndex ? "current" : "upcoming";
          const marker = state === "done" ? "✓" : String(index + 1).padStart(2, "0");
          const clickable = state !== "upcoming";
          return (
            <button
              key={name}
              type="button"
              className={`sidebar__item sidebar__item--${state}`}
              onClick={() => clickable && onSelect(name)}
              disabled={!clickable}
            >
              <span className="sidebar__marker">{marker}</span>
              <span className="sidebar__label">{STAGE_LABELS[name]}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
