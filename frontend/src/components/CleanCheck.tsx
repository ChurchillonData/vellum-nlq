type CleanCheckProps = {
  size?: "sm" | "md" | "lg";
};

export function CleanCheck({ size = "md" }: CleanCheckProps) {
  return <span aria-hidden="true" className={`clean-check clean-check-${size}`} />;
}
