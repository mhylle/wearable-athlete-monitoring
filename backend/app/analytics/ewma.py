"""Exponentially Weighted Moving Average (EWMA) calculations."""


def compute_ewma_single(
    load_today: float, ewma_yesterday: float, decay_days: int
) -> float:
    """Compute a single EWMA value.

    Formula: EWMA_today = Load_today * gamma + (1 - gamma) * EWMA_yesterday
    where gamma = 2 / (N + 1) and N = decay_days.
    """
    gamma = 2.0 / (decay_days + 1)
    return load_today * gamma + (1.0 - gamma) * ewma_yesterday


def compute_ewma(loads: list[float], decay_days: int) -> list[float]:
    """Compute EWMA over a series of daily load values.

    The first value is seeded as the EWMA starting point.
    Returns a list of EWMA values the same length as the input.
    """
    if not loads:
        return []

    result: list[float] = [loads[0]]
    for i in range(1, len(loads)):
        result.append(compute_ewma_single(loads[i], result[i - 1], decay_days))
    return result
