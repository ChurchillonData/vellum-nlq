type SafetyReasonLines = {
  detail?: string;
  summary: string;
};

export function getSafetyReasonLines(reason?: string): SafetyReasonLines {
  const text = (reason ?? "").trim();
  const lowerText = text.toLowerCase();

  if (lowerText.includes("drop") && lowerText.includes("claims")) {
    return {
      detail: "- potential data loss",
      summary: "Command contains DROP + claims"
    };
  }

  if (!text) {
    return { summary: "Potential data loss" };
  }

  const splitAt = text.lastIndexOf(" - ");

  if (splitAt === -1) {
    return { summary: text };
  }

  return {
    detail: `- ${text.slice(splitAt + 3)}`,
    summary: text.slice(0, splitAt)
  };
}

export function getDisplayRuleId(ruleId?: string): string {
  const text = ruleId ?? "";

  if (!text || text.includes("SQL_GUARD_07") || text.includes("DDL_BLOCKLIST")) {
    return "DDL_DROP_PATTERN";
  }

  return text;
}
