import { useEffect, useState } from "react";
import KidSelect from "./pages/KidSelect";
import TopicSelect from "./pages/TopicSelect";
import Session from "./pages/Session";
import Summary from "./pages/Summary";
import Admin from "./pages/Admin";
import type { Kid } from "./api";

export type Page =
  | { name: "kidSelect" }
  | { name: "topicSelect"; kid: Kid }
  | { name: "session"; kid: Kid; topic: string; sessionId: number }
  | { name: "summary"; sessionId: number; kid: Kid; durationSeconds: number }
  | { name: "admin" };

export default function App() {
  const [page, setPage] = useState<Page>({ name: "kidSelect" });

  function navigate(next: Page) {
    history.pushState(next, "");
    setPage(next);
  }

  useEffect(() => {
    history.replaceState({ name: "kidSelect" }, "");
    function onPop(e: PopStateEvent) {
      if (e.state) setPage(e.state as Page);
    }
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "24px" }}>
      {page.name === "kidSelect" && (
        <KidSelect
          onSelect={(kid) => navigate({ name: "topicSelect", kid })}
          onAdmin={() => navigate({ name: "admin" })}
        />
      )}
      {page.name === "admin" && (
        <Admin onBack={() => navigate({ name: "kidSelect" })} />
      )}
      {page.name === "topicSelect" && (
        <TopicSelect
          kid={page.kid}
          onStart={(topic, sessionId) =>
            navigate({ name: "session", kid: page.kid, topic, sessionId })
          }
          onBack={() => navigate({ name: "kidSelect" })}
        />
      )}
      {page.name === "session" && (
        <Session
          kid={page.kid}
          topic={page.topic}
          sessionId={page.sessionId}
          onDone={(duration) => navigate({ name: "summary", sessionId: page.sessionId, kid: page.kid, durationSeconds: duration })}
          onBack={() => navigate({ name: "topicSelect", kid: page.kid })}
        />
      )}
      {page.name === "summary" && (
        <Summary
          sessionId={page.sessionId}
          durationSeconds={page.durationSeconds}
          onPlayAgain={() => navigate({ name: "topicSelect", kid: page.kid })}
          onHome={() => navigate({ name: "kidSelect" })}
        />
      )}
    </div>
  );
}
