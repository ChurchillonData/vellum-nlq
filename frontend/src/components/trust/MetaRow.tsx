import type { ReactNode } from "react";

export function MetaRow({
  compact = false,
  icon,
  label,
  mono = false,
  normalWeight = false,
  tone,
  trailingIcon,
  value
}: {
  compact?: boolean;
  icon?: ReactNode;
  label: string;
  mono?: boolean;
  normalWeight?: boolean;
  tone?: "success" | "warning" | "danger";
  trailingIcon?: ReactNode;
  value: ReactNode;
}) {
  const className = [
    mono ? "mono" : "",
    tone ? `tone-${tone}` : "",
    compact ? "compact-meta" : "",
    normalWeight ? "normal-meta" : ""
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="metadata-row">
      <dt>{label}</dt>
      <dd className={className}>
        {icon && <span className="meta-icon">{icon}</span>}
        <span>{value}</span>
        {trailingIcon && <span className="meta-icon">{trailingIcon}</span>}
      </dd>
    </div>
  );
}
