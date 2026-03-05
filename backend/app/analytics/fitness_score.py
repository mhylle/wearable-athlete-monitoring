"""Composite fitness score computation (0-100) using z-score based metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean, stdev
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.repositories.metric_agg_repo import DailyMetric


@dataclass
class FitnessScore:
    """Composite fitness score with per-component breakdown."""

    total: float | None
    components: dict[str, float] = field(default_factory=dict)
    available_components: list[str] = field(default_factory=list)
    computed_at: datetime = field(default_factory=datetime.utcnow)


# Component weights and directions
# higher_is_better=True means a positive z-score is good
_COMPONENTS = {
    "hrv_rmssd": {"weight": 0.35, "higher_is_better": True, "label": "HRV (RMSSD)"},
    "resting_heart_rate": {"weight": 0.20, "higher_is_better": False, "label": "Resting HR"},
    "sleep_total": {"weight": 0.15, "higher_is_better": True, "label": "Sleep Duration"},
    "sleep_quality": {"weight": 0.10, "higher_is_better": True, "label": "Sleep Quality"},
    "steps": {"weight": 0.10, "higher_is_better": True, "label": "Steps"},
    "hrv_balance": {"weight": 0.05, "higher_is_better": False, "label": "HRV Balance (CV)"},
    "trend_bonus": {"weight": 0.05, "higher_is_better": True, "label": "Trend Bonus"},
}


def _z_score(current_mean: float, baseline_mean: float, baseline_std: float) -> float:
    """Compute z-score of current vs baseline. Returns 0 if std is 0."""
    if baseline_std == 0:
        return 0.0
    return (current_mean - baseline_mean) / baseline_std


def _z_to_score(z: float, higher_is_better: bool) -> float:
    """Convert a z-score to a 0-100 scale.

    z=0 maps to 50 (at baseline).
    z=+2 maps to ~100 for higher-is-better metrics.
    z=-2 maps to ~0 for higher-is-better metrics.
    Inverted for lower-is-better metrics.
    """
    if not higher_is_better:
        z = -z
    # Map z from [-2, +2] to [0, 100], clamped
    score = 50.0 + z * 25.0
    return max(0.0, min(100.0, score))


def compute_fitness_score(
    metric_data: dict[str, list[DailyMetric]],
    trend_bonus: float | None = None,
) -> FitnessScore:
    """Compute a composite fitness score from daily metric aggregates.

    Args:
        metric_data: Dict mapping metric_type -> list of DailyMetric for
                     the full 28-day window. The last 7 days are treated as
                     "current" and the full 28 days as "baseline".
        trend_bonus: Optional trend bonus score (0-100). If None, trend_bonus
                     component is excluded and weights are re-normalized.
    """
    components: dict[str, float] = {}
    available: list[str] = []

    for metric_type, cfg in _COMPONENTS.items():
        if metric_type == "trend_bonus":
            if trend_bonus is not None:
                components["trend_bonus"] = max(0.0, min(100.0, trend_bonus))
                available.append("trend_bonus")
            continue

        if metric_type == "hrv_balance":
            # Derived: coefficient of variation of HRV over recent window
            hrv_data = metric_data.get("hrv_rmssd", [])
            if len(hrv_data) >= 7:
                recent_vals = [d.avg_value for d in hrv_data[-7:]]
                all_vals = [d.avg_value for d in hrv_data]
                if len(recent_vals) >= 2 and mean(recent_vals) > 0:
                    recent_cv = stdev(recent_vals) / mean(recent_vals)
                else:
                    continue
                if len(all_vals) >= 2 and mean(all_vals) > 0:
                    baseline_cv = stdev(all_vals) / mean(all_vals)
                    baseline_cv_std = 0.1  # approximate
                    z = _z_score(recent_cv, baseline_cv, baseline_cv_std)
                    score = _z_to_score(z, cfg["higher_is_better"])
                    components["hrv_balance"] = round(score, 1)
                    available.append("hrv_balance")
            continue

        data = metric_data.get(metric_type, [])
        if len(data) < 7:
            continue

        # Split: last 7 days = current, full range = baseline
        recent_vals = [d.avg_value for d in data[-7:]]
        all_vals = [d.avg_value for d in data]

        current_mean = mean(recent_vals)
        baseline_mean = mean(all_vals)
        baseline_std = stdev(all_vals) if len(all_vals) >= 2 else 0.0

        # Cap sleep_total at 9 hours (540 min) for scoring
        if metric_type == "sleep_total":
            current_mean = min(current_mean, 540.0)
            baseline_mean = min(baseline_mean, 540.0)

        z = _z_score(current_mean, baseline_mean, baseline_std)
        score = _z_to_score(z, cfg["higher_is_better"])
        components[metric_type] = round(score, 1)
        available.append(metric_type)

    if not components:
        return FitnessScore(total=None)

    # Re-weight available components (same pattern as recovery_score.py)
    total_weight = sum(_COMPONENTS[k]["weight"] for k in available)
    total_score = sum(
        components[k] * (_COMPONENTS[k]["weight"] / total_weight) for k in available
    )
    total_score = max(0.0, min(100.0, total_score))

    return FitnessScore(
        total=round(total_score, 1),
        components=components,
        available_components=available,
    )
