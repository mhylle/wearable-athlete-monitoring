"""Training monotony and strain calculations."""

import statistics


def compute_monotony(daily_loads: list[float], window_days: int = 7) -> float:
    """Compute training monotony over a window of daily loads.

    Monotony = mean(daily_loads) / stdev(daily_loads)

    If the standard deviation is zero (all loads identical), returns float('inf').
    Uses the last `window_days` entries from the list.
    """
    window = daily_loads[-window_days:]
    if len(window) < 2:
        return float("inf")

    mean = statistics.mean(window)
    stdev = statistics.pstdev(window)

    if stdev < 1e-10:
        return float("inf")

    return mean / stdev


def compute_strain(weekly_total_load: float, monotony: float) -> float:
    """Compute training strain.

    Strain = weekly_total_load * monotony
    """
    return weekly_total_load * monotony
