import { Code2, Copy } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

type SqlView = "explainable" | "compact";

type TypewriterProfile = {
  initialDelayMs: number;
  intervalMs: number;
  targetDurationMs: number;
};

const TYPEWRITER_PROFILES: Record<SqlView, TypewriterProfile> = {
  explainable: {
    initialDelayMs: 3000,
    intervalMs: 32,
    targetDurationMs: 7200
  },
  compact: {
    initialDelayMs: 3000,
    intervalMs: 32,
    targetDurationMs: 7200
  }
};

export function SqlBlock({
  compactSql,
  sql
}: {
  compactSql?: string | null;
  sql: string;
}) {
  const [activeView, setActiveView] = useState<SqlView>("explainable");
  const hasCompactSql = Boolean(compactSql && compactSql !== sql);
  const activeSql = activeView === "compact" && hasCompactSql ? compactSql ?? sql : sql;
  const { displayedText: displayedSql, isThinking } = useTypewriterText(activeSql, activeView);
  const lines = displayedSql.split("\n");

  return (
    <div className="sql-status">
      <div className="sql-header">
        <span>
          <Code2 className="sql-generated-icon" size={24} />
          Generated SQL (parameterised)
        </span>
        <div className="sql-header-actions">
          {hasCompactSql ? (
            <div aria-label="SQL view" className="sql-view-toggle" role="group">
              <button
                className={activeView === "explainable" ? "active" : ""}
                onClick={() => setActiveView("explainable")}
                type="button"
              >
                Explainable
              </button>
              <button
                className={activeView === "compact" ? "active" : ""}
                onClick={() => setActiveView("compact")}
                type="button"
              >
                Compact
              </button>
            </div>
          ) : null}
          <button
            className="icon-button"
            disabled={!activeSql.trim()}
            onClick={() => void copyText(activeSql)}
            type="button"
          >
            <Copy size={16} />
            Copy
          </button>
        </div>
      </div>
      {isThinking ? (
        <div className="sql-thinking" role="status">
          <span className="sql-thinking-orb" />
          <span>Thinking</span>
          <span className="sql-thinking-dots" aria-hidden="true">
            ...
          </span>
        </div>
      ) : null}
      <div className="sql-frame">
        <div className="line-numbers" aria-hidden="true">
          {lines.map((_, index) => (
            <span key={index}>{index + 1}</span>
          ))}
        </div>
        <pre className="sql-block">
          {lines.map((line, index) => (
            <span className="sql-line" key={`${line}-${index}`}>
              {highlightSqlLine(line)}
              {index < lines.length - 1 ? "\n" : ""}
            </span>
          ))}
          {displayedSql.length < activeSql.length ? <span className="sql-caret" /> : null}
        </pre>
      </div>
    </div>
  );
}

function useTypewriterText(text: string, view: SqlView) {
  const [displayedText, setDisplayedText] = useState("");
  const [isThinking, setIsThinking] = useState(false);

  useEffect(() => {
    if (!text) {
      setDisplayedText("");
      setIsThinking(false);
      return;
    }

    if (prefersReducedMotion()) {
      setDisplayedText(text);
      setIsThinking(false);
      return;
    }

    setDisplayedText("");
    setIsThinking(true);
    const profile = TYPEWRITER_PROFILES[view];
    let cursor = 0;
    const targetTicks = Math.max(1, Math.ceil(profile.targetDurationMs / profile.intervalMs));
    const chunkSize = Math.max(1, Math.ceil(text.length / targetTicks));
    let timer: number | undefined;

    const delay = window.setTimeout(() => {
      timer = window.setInterval(() => {
        setIsThinking(false);
        cursor = Math.min(text.length, cursor + chunkSize);
        setDisplayedText(text.slice(0, cursor));

        if (cursor >= text.length && timer !== undefined) {
          window.clearInterval(timer);
        }
      }, profile.intervalMs);
    }, profile.initialDelayMs);

    return () => {
      window.clearTimeout(delay);
      if (timer !== undefined) {
        window.clearInterval(timer);
      }
    };
  }, [text, view]);

  return { displayedText, isThinking };
}

function prefersReducedMotion() {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}

async function copyText(text: string): Promise<void> {
  if (!text.trim()) {
    return;
  }

  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.setAttribute("readonly", "");
  textArea.style.position = "fixed";
  textArea.style.opacity = "0";
  document.body.appendChild(textArea);
  textArea.select();
  document.execCommand("copy");
  document.body.removeChild(textArea);
}

const sqlKeywords = new Set([
  "AND",
  "AS",
  "BETWEEN",
  "BY",
  "FROM",
  "GROUP",
  "JOIN",
  "ON",
  "SELECT",
  "USING",
  "WHERE",
  "WITH"
]);

const sqlFunctions = new Set(["COUNT", "SUM", "AVG", "MIN", "MAX", "NULLIF"]);

function highlightSqlLine(line: string): ReactNode[] {
  const commentStart = line.indexOf("--");

  if (commentStart === 0) {
    return [<span className="sql-comment" key="comment">{line}</span>];
  }

  if (commentStart > 0) {
    return [
      ...highlightSqlLine(line.slice(0, commentStart)),
      <span className="sql-comment" key="comment">{line.slice(commentStart)}</span>
    ];
  }

  return line
    .split(/('[^']*'|\b\d+(?:\.\d+)?\b|\b[A-Za-z_][A-Za-z0-9_]*\b)/g)
    .map((part, index) => {
      if (!part) {
        return part;
      }

      if (/^'[^']*'$/.test(part)) {
        return <span className="sql-string" key={`${part}-${index}`}>{part}</span>;
      }

      if (/^\d+(?:\.\d+)?$/.test(part)) {
        return <span className="sql-number" key={`${part}-${index}`}>{part}</span>;
      }

      if (sqlKeywords.has(part.toUpperCase())) {
        return <span className="sql-keyword" key={`${part}-${index}`}>{part}</span>;
      }

      if (sqlFunctions.has(part.toUpperCase())) {
        return <span className="sql-function" key={`${part}-${index}`}>{part}</span>;
      }

      return part;
    });
}
