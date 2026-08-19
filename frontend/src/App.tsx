import { useState } from "react";
import { createSession, sendMessage } from "./api";
import type { MessageResponseOk } from "./types";
import { IdeaIntake } from "./components/IdeaIntake";
import { PipelineView } from "./components/PipelineView";
import "./App.css";

interface Warning {
  message: string;
  rawText: string;
}

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [idea, setIdea] = useState("");
  const [stageIndex, setStageIndex] = useState(0);
  const [complete, setComplete] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<MessageResponseOk[]>([]);
  const [warning, setWarning] = useState<Warning | null>(null);

  // Auto-advances through the whole pipeline: after each stage succeeds it
  // immediately calls itself for the next one, so the user only interacts
  // once (submitting the idea). It only stops on completion or a warning
  // (which surfaces a retry button rather than looping forever on an error).
  const runStage = async (id: string): Promise<void> => {
    setLoading(true);
    try {
      const res = await sendMessage(id, "");
      if (res.status === "warning") {
        setWarning({ message: res.warning, rawText: res.raw_text });
        return;
      }
      setWarning(null);
      setResults((prev) => [...prev, res]);
      setStageIndex(res.stage_index);
      setComplete(res.complete);
      if (!res.complete) {
        await runStage(id);
      }
    } catch (err) {
      setWarning({
        message: "서버와 통신하지 못했습니다. 백엔드가 실행 중인지 확인해주세요.",
        rawText: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (submittedIdea: string) => {
    setLoading(true);
    setIdea(submittedIdea);
    try {
      const session = await createSession(submittedIdea);
      setSessionId(session.session_id);
      await runStage(session.session_id);
    } catch (err) {
      setWarning({
        message: "세션을 시작하지 못했습니다. 백엔드가 실행 중인지 확인해주세요.",
        rawText: err instanceof Error ? err.message : String(err),
      });
      setLoading(false);
    }
  };

  const handleRetry = () => {
    if (!sessionId) return;
    runStage(sessionId);
  };

  if (!sessionId) {
    return <IdeaIntake onSubmit={handleStart} disabled={loading} />;
  }

  return (
    <PipelineView
      idea={idea}
      stageIndex={stageIndex}
      complete={complete}
      loading={loading}
      results={results}
      warning={warning}
      onRetry={handleRetry}
    />
  );
}

export default App;
