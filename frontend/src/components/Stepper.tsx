import { STAGE_LABELS, STAGE_NAMES } from "../types";
import "./Stepper.css";

interface StepperProps {
  currentIndex: number;
}

export function Stepper({ currentIndex }: StepperProps) {
  return (
    <ol className="stepper">
      {STAGE_NAMES.map((name, index) => {
        const state =
          index < currentIndex ? "done" : index === currentIndex ? "current" : "upcoming";
        return (
          <li key={name} className={`stepper__item stepper__item--${state}`}>
            <span className="stepper__marker">
              {state === "done" ? "✓" : String(index + 1).padStart(2, "0")}
            </span>
            <span className="stepper__label">{STAGE_LABELS[name]}</span>
          </li>
        );
      })}
    </ol>
  );
}
