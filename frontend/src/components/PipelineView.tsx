import { STAGE_LABELS, type MessageResponseOk, type StageName } from "../types";
import { buildMarkdownReport, downloadMarkdown } from "../markdown";
import { SidebarNav } from "./SidebarNav";
import { StageOutputView } from "./StageOutputView";
import "./PipelineView.css";

interface PipelineViewProps {
  idea: string;
  stageIndex: number;
  complete: boolean;
  loading: boolean;
  results: MessageResponseOk[];
  warning: { message: string; rawText: string } | null;
  onRetry: () => void;
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
  onRetry,
}: PipelineViewProps) {
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
    <div className="board">
      <SidebarNav idea={idea} currentIndex={stageIndex} onSelect={handleSelectStage} />

      <main className="board__main">
        <div className="board__grid">
          {results.map((result, index) => (
            <section
              key={result.stage_name}
              id={stageAnchorId(result.stage_name)}
              className="board__card"
            >
              <p className="eyebrow board__card-eyebrow">
                STAGE {String(index + 1).padStart(2, "0")} · {STAGE_LABELS[result.stage_name]}
              </p>
              <StageOutputView stageName={result.stage_name} output={result.output} />
            </section>
          ))}
        </div>

        {loading && (
          <div className="board__active">
            <div className="board__loading">
              <span className="board__loading-dot" />
              <span>{LOADING_COPY[stageIndex] ?? "분석하는 중입니다…"}</span>
            </div>
          </div>
        )}

        {!loading && warning && (
          <div className="board__active">
            <div className="board__warning">
              <p className="board__warning-title">이번 응답을 정리하지 못했습니다</p>
              <p className="board__warning-message">{warning.message}</p>
              <details className="board__warning-raw">
                <summary>원본 응답 보기</summary>
                <pre>{warning.rawText}</pre>
              </details>
              <button type="button" className="board__retry-btn" onClick={onRetry}>
                다시 시도
              </button>
            </div>
          </div>
        )}

        {complete && (
          <div className="board__complete">
            <p>8단계 프로토콜이 모두 완료됐습니다.</p>
            <button type="button" className="board__download-btn" onClick={handleDownload}>
              마크다운으로 저장
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
