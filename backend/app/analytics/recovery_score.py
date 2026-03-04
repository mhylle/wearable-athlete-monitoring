"""Composite recovery score computation (inspired by WHOOP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.analytics.acwr import ACWRResult
    from app.analytics.hrv import HRVStats
    from app.analytics.sleep import SleepSummary


@dataclass
class WellnessInput:
    """Minimal wellness data needed for recovery score computation."""

    mood: int | None = None
    soreness: int | None = None
    fatigue: int | None = None


@dataclass
class RecoveryScore:
    """Composite recovery score with per-component breakdown."""

    total_score: float | None
    hrv_component: float | None = None
    sleep_component: float | None = None
    load_component: float | None = None
    subjective_component: float | None = None
    available_components: list[str] = field(default_factory=list)


# Default component weights
_WEIGHTS = {
    "hrv": 0.40,
    "sleep": 0.30,
    "load": 0.20,
    "subjective": 0.10,
}

# Target sleep duration in minutes (8 hours)
_SLEEP_TARGET_MINUTES = 480.0


def compute_recovery_score(
    hrv_stats: HRVStats | None,
    sleep_summary: SleepSummary | None,
    acwr_result: ACWRResult | None,
    wellness: WellnessInput | None,
) -> RecoveryScore:
    """Compute a composite recovery score (0-100) from available data.

    Components:
        HRV (40%): current RMSSD vs 30-day baseline.
        Sleep (30%): sleep quality (efficiency) + duration vs 8h target.
        Training load (20%): inverse ACWR deviation from 1.0.
        Subjective (10%): average of mood, inverse soreness, inverse fatigue.

    Missing components are excluded and remaining weights are re-normalized.
    """
    components: dict[str, float] = {}
    available: list[str] = []

    # HRV component (0-100)
    if hrv_stats is not None and hrv_stats.baseline_mean > 0:
        hrv_score = _compute_hrv_component(hrv_stats)
        components["hrv"] = hrv_score
        available.append("hrv")

    # Sleep component (0-100)
    if sleep_summary is not None and sleep_summary.total_minutes > 0:
        sleep_score = _compute_sleep_component(sleep_summary)
        components["sleep"] = sleep_score
        available.append("sleep")

    # Training load component (0-100)
    if acwr_result is not None and acwr_result.acwr_value is not None:
        load_score = _compute_load_component(acwr_result)
        components["load"] = load_score
        available.append("load")

    # Subjective component (0-100)
    if wellness is not None:
        subj_score = _compute_subjective_component(wellness)
        if subj_score is not None:
            components["subjective"] = subj_score
            available.append("subjective")

    if not components:
        return RecoveryScore(
            total_score=None,
            available_components=[],
        )

    # Re-weight available components
    total_weight = sum(_WEIGHTS[k] for k in available)
    total_score = sum(
        components[k] * (_WEIGHTS[k] / total_weight) for k in available
    )

    total_score = max(0.0, min(100.0, total_score))

    return RecoveryScore(
        total_score=round(total_score, 1),
        hrv_component=round(components["hrv"], 1) if "hrv" in components else None,
        sleep_component=round(components["sleep"], 1) if "sleep" in components else None,
        load_component=round(components["load"], 1) if "load" in components else None,
        subjective_component=(
            round(components["subjective"], 1) if "subjective" in components else None
        ),
        available_components=available,
    )


def _compute_hrv_component(hrv_stats: HRVStats) -> float:
    """HRV component: current rolling mean vs baseline mean.

    Score 100 if rolling mean >= baseline * 1.1 (10% above).
    Score 50 if rolling mean == baseline.
    Score 0 if rolling mean <= baseline * 0.7 (30% below).
    Linear interpolation between these anchors.
    """
    ratio = hrv_stats.rolling_mean / hrv_stats.baseline_mean if hrv_stats.baseline_mean > 0 else 1.0

    if ratio >= 1.1:
        return 100.0
    if ratio <= 0.7:
        return 0.0

    # Linear scale: 0.7 -> 0, 1.0 -> 50, 1.1 -> 100
    if ratio <= 1.0:
        return ((ratio - 0.7) / 0.3) * 50.0
    return 50.0 + ((ratio - 1.0) / 0.1) * 50.0


def _compute_sleep_component(sleep_summary: SleepSummary) -> float:
    """Sleep component: combination of efficiency and duration.

    Duration score (50%): sleep minutes / target (8h), capped at 100.
    Efficiency score (50%): efficiency * 100.
    """
    duration_ratio = min(sleep_summary.total_minutes / _SLEEP_TARGET_MINUTES, 1.0)
    duration_score = duration_ratio * 100.0
    efficiency_score = sleep_summary.efficiency * 100.0

    return 0.5 * duration_score + 0.5 * efficiency_score


def _compute_load_component(acwr_result: ACWRResult) -> float:
    """Training load component: inverse deviation of ACWR from optimal (1.0).

    Score 100 if ACWR == 1.0 (perfect).
    Score decreases linearly: 0 deviation -> 100, 1.0 deviation -> 0.
    """
    if acwr_result.acwr_value is None:
        return 50.0

    deviation = abs(acwr_result.acwr_value - 1.0)
    score = max(0.0, 100.0 * (1.0 - deviation))
    return score


def _compute_subjective_component(wellness: WellnessInput) -> float | None:
    """Subjective component: average of mood, inverse soreness, inverse fatigue.

    Mood: 1-5 scale, higher is better -> normalize to 0-100.
    Soreness: 1-10 scale, lower is better -> invert (11 - value) / 10 * 100.
    Fatigue: 1-10 scale, lower is better -> invert (11 - value) / 10 * 100.
    """
    scores: list[float] = []

    if wellness.mood is not None:
        scores.append((wellness.mood - 1) / 4.0 * 100.0)

    if wellness.soreness is not None:
        scores.append((11 - wellness.soreness) / 10.0 * 100.0)

    if wellness.fatigue is not None:
        scores.append((11 - wellness.fatigue) / 10.0 * 100.0)

    if not scores:
        return None

    return sum(scores) / len(scores)
