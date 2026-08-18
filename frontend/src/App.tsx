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

  const runStage = async (id: string, message: string) => {
    setLoading(true);
    try {
      const res = await sendMessage(id, message);
      if (res.status === "warning") {
        setWarning({ message: res.warning, rawText: res.raw_text });
      } else {
        setWarning(null);
        setResults((prev) => [...prev, res]);
        setStageIndex(res.stage_index);
        setComplete(res.complete);
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
      await runStage(session.session_id, "");
    } catch (err) {
      setWarning({
        message: "세션을 시작하지 못했습니다. 백엔드가 실행 중인지 확인해주세요.",
        rawText: err instanceof Error ? err.message : String(err),
      });
      setLoading(false);
    }
  };

  const handleAdvance = (message: string) => {
    if (!sessionId) return;
    runStage(sessionId, message);
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
      onAdvance={handleAdvance}
    />
  );
}

export default App;
