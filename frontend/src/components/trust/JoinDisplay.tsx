export function JoinDisplay({ joins }: { joins?: string[] }) {
  const joined = joins?.join("; ") ?? "claims -> premium (member_id)";

  if (joined.includes("claims") && joined.includes("premium")) {
    return (
      <span className="join-display">
        <span>claims</span>
        <JoinBranchMark />
        <span>premium</span>
        <span className="join-key">(member_id)</span>
      </span>
    );
  }

  return <span>{joined.replace(/->|â†’/g, "âŸ•")}</span>;
}

function JoinBranchMark() {
  return (
    <svg
      aria-label="left join"
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
