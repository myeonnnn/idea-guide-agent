import { useState } from "react";
import { STAGE_LABELS, type MessageResponseOk } from "../types";
import { Stepper } from "./Stepper";
import { StageOutputView } from "./StageOutputView";
import "./PipelineView.css";

interface PipelineViewProps {
  idea: string;
  stageIndex: number;
  complete: boolean;
  loading: boolean;
  result: MessageResponseOk | null;
  warning: { message: string; rawText: string } | null;
  onAdvance: (message: string) => void;
}

const LOADING_COPY: Record<number, string> = {
  0: "시장을 조사하는 중입니다…",
  1: "타겟 고객층을 분석하는 중입니다…",
  2: "검증 가능한 가설을 세우는 중입니다…",
  3: "가설 검증 계획을 구체화하는 중입니다…",
  4: "MVP/MLP 범위를 정의하는 중입니다…",
  5: "비즈니스모델을 구조화하는 중입니다…",
};

export function PipelineView({
  idea,
  stageIndex,
  complete,
  loading,
  result,
  warning,
  onAdvance,
}: PipelineViewProps) {
  const [message, setMessage] = useState("");

  const handleAdvance = () => {
    onAdvance(message);
    setMessage("");
  };

  return (
    <div className="pipeline">
      <p className="pipeline__idea">
        <span className="mono-label">아이디어</span> {idea}
      </p>

      <Stepper currentIndex={stageIndex} />

      <div className="pipeline__card">
        {loading ? (
          <div className="pipeline__loading">
            <span className="pipeline__loading-dot" />
            <span>{LOADING_COPY[stageIndex] ?? "분석하는 중입니다…"}</span>
          </div>
        ) : warning ? (
          <div className="pipeline__warning">
            <p className="pipeline__warning-title">이번 응답을 정리하지 못했습니다</p>
            <p className="pipeline__warning-message">{warning.message}</p>
            <details className="pipeline__warning-raw">
              <summary>원본 응답 보기</summary>
              <pre>{warning.rawText}</pre>
            </details>
          </div>
        ) : (
          result && (
            <>
              <p className="eyebrow pipeline__card-eyebrow">
                STAGE {String(stageIndex).padStart(2, "0")} · {STAGE_LABELS[result.stage_name]}
              </p>
              <StageOutputView stageName={result.stage_name} output={result.output} />
            </>
          )
        )}
      </div>

      {!complete && !loading && (
        <div className="pipeline__next">
          <input
            className="pipeline__input"
            type="text"
            placeholder="추가로 반영하고 싶은 내용이 있다면 입력하세요 (선택)"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdvance()}
          />
          <button type="button" className="pipeline__next-btn" onClick={handleAdvance}>
            {warning ? "다시 시도" : "다음 단계"}
          </button>
        </div>
      )}

      {complete && (
        <p className="pipeline__complete">6단계 프로토콜이 모두 완료됐습니다.</p>
      )}
    </div>
  );
}
