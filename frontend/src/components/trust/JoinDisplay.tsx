type ParsedJoin = {
  left: string;
  right: string;
  cardinality: string | null;
};

export function JoinDisplay({ joins }: { joins?: string[] }) {
  if (!joins || joins.length === 0) {
    return <span className="join-empty">No joins used</span>;
  }

  return (
    <span className="join-list">
      {joins.map((join) => (
        <JoinEdgeDisplay join={join} key={join} />
      ))}
    </span>
  );
}

function JoinEdgeDisplay({ join }: { join: string }) {
  const parsed = parseJoin(join);

  if (!parsed) {
    return <span className="join-edge">{join}</span>;
  }

  return (
    <span className="join-edge">
      <span>{parsed.left}</span>
      <JoinBranchMark />
      <span>{parsed.right}</span>
      {parsed.cardinality ? (
        <span className="join-cardinality">{parsed.cardinality}</span>
      ) : null}
    </span>
  );
}

function parseJoin(join: string): ParsedJoin | null {
  const match = join.match(/^(.+?)\s=\s(.+?)(?:\s\((.+)\))?$/);

  if (!match) {
    return null;
  }

  return {
    left: match[1],
    right: match[2],
    cardinality: match[3] ?? null
  };
}

function JoinBranchMark() {
  return (
    <svg
      aria-label="join link"
      className="join-branch-mark"
      fill="none"
      height="16"
      viewBox="0 0 22 16"
      width="22"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M4 3v10M4 8h14"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.8"
      />
      <circle cx="4" cy="3" fill="currentColor" r="1.8" />
      <circle cx="18" cy="8" fill="currentColor" r="1.8" />
      <circle cx="4" cy="13" fill="currentColor" r="1.8" />
    </svg>
  );
}
