import { useState } from "react";
import { STAGE_LABELS, type MessageResponseOk, type StageName } from "../types";
import { buildMarkdownReport, downloadMarkdown } from "../markdown";
import { Stepper } from "./Stepper";
import { StageOutputView } from "./StageOutputView";
import "./PipelineView.css";

interface PipelineViewProps {
  idea: string;
  stageIndex: number;
  complete: boolean;
  loading: boolean;
  results: MessageResponseOk[];
  warning: { message: string; rawText: string } | null;
  onAdvance: (message: string) => void;
}

const LOADING_COPY: Record<number, string> = {
  0: "타겟 고객층을 분석하는 중입니다…",
  1: "시장을 조사하는 중입니다…",
  2: "가치제안과 차별화 우위를 정리하는 중입니다…",
  3: "검증 가능한 가설을 세우는 중입니다…",
  4: "가장 위험한 가정을 가려내는 중입니다…",
  5: "MVP/MLP 범위를 정의하는 중입니다…",
  6: "비즈니스모델을 구조화하는 중입니다…",
  7: "지금까지의 결과를 종합해 판단하는 중입니다…",
};

function stageAnchorId(name: StageName): string {
  return `stage-${name}`;
}

export function PipelineView({
  idea,
  stageIndex,
  complete,
  loading,
  results,
  warning,
  onAdvance,
}: PipelineViewProps) {
  const [message, setMessage] = useState("");

  const handleAdvance = () => {
    onAdvance(message);
    setMessage("");
  };

  const handleSelectStage = (name: StageName) => {
    document.getElementById(stageAnchorId(name))?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const handleDownload = () => {
    const report = buildMarkdownReport(idea, results);
    const date = new Date().toISOString().slice(0, 10);
    downloadMarkdown(`아이디어검증_${date}.md`, report);
  };

  return (
    <div className="pipeline">
      <p className="pipeline__idea">
        <span className="mono-label">아이디어</span> {idea}
      </p>

      <div className="pipeline__stepper-row">
        <Stepper currentIndex={stageIndex} onSelect={handleSelectStage} />
      </div>

      <div className="pipeline__timeline">
        {results.map((result, index) => (
          <section
            key={result.stage_name}
            id={stageAnchorId(result.stage_name)}
            className="pipeline__card"
          >
            <p className="eyebrow pipeline__card-eyebrow">
              STAGE {String(index + 1).padStart(2, "0")} · {STAGE_LABELS[result.stage_name]}
            </p>
            <StageOutputView stageName={result.stage_name} output={result.output} />
          </section>
        ))}

        {(loading || warning) && (
          <div className="pipeline__card">
            {loading ? (
              <div className="pipeline__loading">
                <span className="pipeline__loading-dot" />
                <span>{LOADING_COPY[stageIndex] ?? "분석하는 중입니다…"}</span>
              </div>
            ) : (
              warning && (
                <div className="pipeline__warning">
                  <p className="pipeline__warning-title">이번 응답을 정리하지 못했습니다</p>
                  <p className="pipeline__warning-message">{warning.message}</p>
                  <details className="pipeline__warning-raw">
                    <summary>원본 응답 보기</summary>
                    <pre>{warning.rawText}</pre>
                  </details>
                </div>
              )
            )}
          </div>
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
        <div className="pipeline__complete">
          <p>8단계 프로토콜이 모두 완료됐습니다.</p>
          <button type="button" className="pipeline__download-btn" onClick={handleDownload}>
            마크다운으로 저장
          </button>
        </div>
      )}
    </div>
  );
}
