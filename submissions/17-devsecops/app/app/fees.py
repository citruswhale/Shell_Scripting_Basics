"""Late fee rules for overdue equipment loans."""

# The fee never goes above this, even for very late returns
MAX_FEE = 500.0
# First day late is free (grace period)
GRACE_DAYS = 1


def late_fee(days_late: int, daily_rate: float) -> float:
    """Return the late fee in rupees, rounded to 2 decimals and capped at MAX_FEE."""
    if days_late < 0:
        raise ValueError("days_late cannot be negative")
    if daily_rate < 0:
        raise ValueError("daily_rate cannot be negative")
    chargeable_days = max(0, days_late - GRACE_DAYS)
    return round(min(chargeable_days * daily_rate, MAX_FEE), 2)
