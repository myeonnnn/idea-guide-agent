import { STAGE_LABELS, STAGE_NAMES, type StageName } from "../types";
import "./Stepper.css";

interface StepperProps {
  currentIndex: number;
  onSelect?: (name: StageName) => void;
}

export function Stepper({ currentIndex, onSelect }: StepperProps) {
  return (
    <ol className="stepper">
      {STAGE_NAMES.map((name, index) => {
        const state =
          index < currentIndex ? "done" : index === currentIndex ? "current" : "upcoming";
        const clickable = state !== "upcoming" && onSelect;
        const marker = state === "done" ? "✓" : String(index + 1).padStart(2, "0");
        return (
          <li key={name} className={`stepper__item stepper__item--${state}`}>
            {clickable ? (
              <button
                type="button"
                className="stepper__button"
                onClick={() => onSelect(name)}
              >
                <span className="stepper__marker">{marker}</span>
                <span className="stepper__label">{STAGE_LABELS[name]}</span>
              </button>
            ) : (
              <span className="stepper__button">
                <span className="stepper__marker">{marker}</span>
                <span className="stepper__label">{STAGE_LABELS[name]}</span>
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
