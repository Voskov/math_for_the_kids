import { useState } from "react";
import KidSelect from "./pages/KidSelect";
import TopicSelect from "./pages/TopicSelect";
import Session from "./pages/Session";
import Summary from "./pages/Summary";
import type { Kid } from "./api";

export type Page =
  | { name: "kidSelect" }
  | { name: "topicSelect"; kid: Kid }
  | { name: "session"; kid: Kid; topic: string; sessionId: number }
  | { name: "summary"; sessionId: number; kid: Kid };

export default function App() {
  const [page, setPage] = useState<Page>({ name: "kidSelect" });

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "24px" }}>
      {page.name === "kidSelect" && (
        <KidSelect
          onSelect={(kid) => setPage({ name: "topicSelect", kid })}
        />
      )}
      {page.name === "topicSelect" && (
        <TopicSelect
          kid={page.kid}
          onStart={(topic, sessionId) =>
            setPage({ name: "session", kid: page.kid, topic, sessionId })
          }
          onBack={() => setPage({ name: "kidSelect" })}
        />
      )}
      {page.name === "session" && (
        <Session
          kid={page.kid}
          topic={page.topic}
          sessionId={page.sessionId}
          onDone={() => setPage({ name: "summary", sessionId: page.sessionId, kid: page.kid })}
        />
      )}
      {page.name === "summary" && (
        <Summary
          sessionId={page.sessionId}
          onPlayAgain={() => setPage({ name: "topicSelect", kid: page.kid })}
          onHome={() => setPage({ name: "kidSelect" })}
        />
      )}
    </div>
  );
}
