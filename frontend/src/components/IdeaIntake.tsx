import { useState, type FormEvent } from "react";
import { STAGE_LABELS, STAGE_NAMES } from "../types";
import "./IdeaIntake.css";

interface IdeaIntakeProps {
  onSubmit: (idea: string) => void;
  disabled: boolean;
}

export function IdeaIntake({ onSubmit, disabled }: IdeaIntakeProps) {
  const [idea, setIdea] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = idea.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  };

  return (
    <div className="intake">
      <p className="intake__eyebrow">아이디어 검증 에이전트</p>
      <h1 className="intake__headline">
        만들기 전에,
        <br />
        먼저 검증하세요.
      </h1>
      <p className="intake__subhead">
        타겟층 설정부터 종합 판단까지 8단계 프로토콜로 아이디어를 검토합니다. 모든 주장에는
        출처 등급이 붙고, 가장 위험한 가정을 가려내며, 마지막엔 진행/피벗/보류를 냉정하게
        판단합니다.
      </p>

      <form className="intake__form" onSubmit={handleSubmit}>
        <textarea
          className="intake__textarea"
          placeholder="예: 바쁜 1인 가구를 위한 반려동물 산책 대행 매칭 서비스"
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          rows={4}
          disabled={disabled}
          autoFocus
        />
        <button
          type="submit"
          className="intake__submit"
          disabled={disabled || idea.trim().length === 0}
        >
          검증 시작
        </button>
      </form>

      <ol className="intake__protocol">
        {STAGE_NAMES.map((name, i) => (
          <li key={name}>
            <span className="intake__protocol-index">{String(i + 1).padStart(2, "0")}</span>
            {STAGE_LABELS[name]}
          </li>
        ))}
      </ol>
    </div>
  );
}
