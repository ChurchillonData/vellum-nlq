export function formatSafetyReason(reason?: string): string {
  const text = reason ?? "";
  const lowerText = text.toLowerCase();

  if (lowerText.includes("drop") && lowerText.includes("claims")) {
    return "Command contains DROP + claims · potential data loss";
  }

  if (!text.trim()) {
    return "Potential data loss";
  }

  return text.replace(/\s+-\s+/g, " · ");
}

export function getDisplayRuleId(ruleId?: string): string {
  const text = ruleId ?? "";

  if (!text || text.includes("SQL_GUARD_07") || text.includes("DDL_BLOCKLIST")) {
    return "DDL_DROP_PATTERN";
  }

  return text;
}
