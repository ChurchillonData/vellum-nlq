import calendar
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class DataWindow:
    """Historical data period available to the demo analytics engine."""

    as_of_date: date
    start_date: date
    end_date: date
    month_count: int

    def contains(self, start_date: date, end_date: date) -> bool:
        """Return whether a requested period is fully available."""
        return self.start_date <= start_date <= end_date <= self.end_date


@dataclass(frozen=True)
class PeriodAvailability:
    """Availability result for one requested analytics period."""

    available: bool
    reason_id: str | None = None
    message: str | None = None


def rolling_data_window(
    as_of_date: date | None = None,
    month_count: int = 18,
) -> DataWindow:
    """Return the last completed months available to the demo dataset."""
    if month_count < 1:
        raise ValueError("month_count must be at least 1")

    anchor = as_of_date or date.today()
    current_month = date(anchor.year, anchor.month, 1)
    latest_month = add_months(current_month, -1)
    start_month = add_months(latest_month, -(month_count - 1))

    return DataWindow(
        as_of_date=anchor,
        start_date=start_month,
        end_date=month_end(latest_month.year, latest_month.month),
        month_count=month_count,
    )


def latest_completed_quarter(as_of_date: date | None = None) -> tuple[date, date]:
    """Return the latest fully completed calendar quarter."""
    anchor = as_of_date or date.today()
    current_quarter_month = ((anchor.month - 1) // 3 * 3) + 1
    current_quarter_start = date(anchor.year, current_quarter_month, 1)
    previous_quarter_end = current_quarter_start - timedelta(days=1)
    previous_quarter_month = ((previous_quarter_end.month - 1) // 3 * 3) + 1
    previous_quarter_start = date(previous_quarter_end.year, previous_quarter_month, 1)
    return previous_quarter_start, previous_quarter_end


def check_period_available(
    start_date: date,
    end_date: date,
    window: DataWindow,
) -> PeriodAvailability:
    """Check whether a requested period is inside the available data window."""
    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date")

    if window.contains(start_date, end_date):
        return PeriodAvailability(available=True)

    return PeriodAvailability(
        available=False,
        reason_id="period_outside_data_window",
        message=(
            "Requested period is outside the available demo data window "
            f"({window.start_date.isoformat()} to {window.end_date.isoformat()})."
        ),
    )


def add_months(value: date, offset: int) -> date:
    """Add calendar months while keeping the result at month start."""
    month_index = value.month - 1 + offset
    return date(value.year + month_index // 12, (month_index % 12) + 1, 1)


def month_end(year: int, month: int) -> date:
    """Return the final day of a calendar month."""
    return date(year, month, calendar.monthrange(year, month)[1])
