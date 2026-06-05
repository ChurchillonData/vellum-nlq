import argparse

from app.portfolio.audit import PortfolioAuditReport, audit_generated_portfolio
from app.portfolio.live import LivePortfolioAuditReport, audit_live_portfolio


def parse_args() -> argparse.Namespace:
    """Parse portfolio audit command options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Audit a seeded Postgres portfolio.")
    parser.add_argument("--member-count", type=int, default=200_000)
    parser.add_argument("--month-count", type=int, default=18)
    parser.add_argument("--chunk-size", type=int, default=10_000)
    parser.add_argument("--max-latency-ms", type=float, default=5_000)
    return parser.parse_args()


def main() -> None:
    """Run and print either the generated-data or live-Postgres portfolio audit."""
    args = parse_args()

    report: PortfolioAuditReport | LivePortfolioAuditReport
    if args.live:
        report = audit_live_portfolio(max_latency_ms=args.max_latency_ms)
    else:
        report = audit_generated_portfolio(
            member_count=args.member_count,
            month_count=args.month_count,
            chunk_size=args.chunk_size,
        )

    print_report(report)
    if not report.passed:
        raise SystemExit(1)


def print_report(report: PortfolioAuditReport | LivePortfolioAuditReport) -> None:
    """Print concise audit checks and generation performance."""
    for check in report.checks:
        status = "ok" if check.passed else "failed"
        print(
            f"{check.name}: {status} - observed {check.observed}; "
            f"expected {check.expected}"
        )

    if isinstance(report, PortfolioAuditReport):
        summary = report.summary
        print(f"generation: {summary.generation_seconds:,.2f} seconds")
        print(f"throughput: {summary.generated_rows_per_second:,} rows/second")


if __name__ == "__main__":
    main()
