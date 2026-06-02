import { Code2, Copy } from "lucide-react";
import { useState, type ReactNode } from "react";

type SqlView = "explainable" | "compact";

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
  const lines = activeSql.split("\n");

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
            onClick={() => navigator.clipboard.writeText(activeSql)}
            type="button"
          >
            <Copy size={16} />
            Copy
          </button>
        </div>
      </div>
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
        </pre>
      </div>
    </div>
  );
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
