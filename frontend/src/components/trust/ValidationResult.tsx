import { AlertTriangle } from "lucide-react";
import { useEffect, useState } from "react";

import type { Validation } from "../../types";
import { CleanCheck } from "../CleanCheck";

export function ValidationResult({ validation }: { validation?: Validation }) {
  if (!validation) {
    return <span>pending</span>;
  }

  if (!validation.passed) {
    return <ValidationFailures validation={validation} />;
  }

  return <ValidationPass validation={validation} />;
}

export function ValidationStatusIcon({ validation }: { validation?: Validation }) {
  if (validation?.passed === false) {
    return (
      <span className="validation-result-alert">
        <AlertTriangle size={13} />
      </span>
    );
  }

  return (
    <span className="validation-result-check">
      <CleanCheck size="sm" />
    </span>
  );
}

function ValidationPass({ validation }: { validation: Validation }) {
  const checkedCount = useCountingNumber(validation.rules_checked.length);

  return (
    <span className="validation-result-detail">
      <span>
        {checkedCount} of {validation.rules_checked.length} rules checked - no violations
      </span>
      <ol className="validation-rule-list" aria-label="Checked validation rules">
        {validation.rules_checked.map((rule) => (
          <li key={rule}>{humaniseRule(rule)}</li>
        ))}
      </ol>
    </span>
  );
}

function ValidationFailures({ validation }: { validation: Validation }) {
  const violationCount = validation.rejections.length;

  return (
    <span className="validation-result-detail">
      <span>
        blocked - {violationCount} {violationCount === 1 ? "violation" : "violations"}
      </span>
      <ol className="validation-rule-list violation-list" aria-label="Validation violations">
        {validation.rejections.map((rejection) => (
          <li key={`${rejection.rule}-${rejection.message}`}>
            <strong>{rejection.rule}</strong>: {rejection.message}
          </li>
        ))}
      </ol>
    </span>
  );
}

function useCountingNumber(target: number) {
  const [value, setValue] = useState(target > 0 ? 1 : 0);

  useEffect(() => {
    if (target <= 1) {
      setValue(target);
      return;
    }

    setValue(1);
    const timer = window.setInterval(() => {
      setValue((current) => {
        const next = current + 1;

        if (next >= target) {
          window.clearInterval(timer);
          return target;
        }

        return next;
      });
    }, 35);

    return () => window.clearInterval(timer);
  }, [target]);

  return value;
}

function humaniseRule(rule: string) {
  return rule.replace(/_/g, " ");
}
