"""Seed script: generates 90 days of realistic demo data.

Usage:
    python -m app.db.seed
"""

from __future__ import annotations

import asyncio
import random
import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.password import hash_password
from app.config import settings
from app.models.athlete_profile import AthleteProfile
from app.models.metric_record import MetricRecord
from app.models.session_metrics import SessionMetrics
from app.models.team import Team
from app.models.training_session import TrainingSession
from app.models.user import User
from app.models.wellness_entry import WellnessEntry

# ---------- configuration ----------

NUM_ATHLETES = 25
NUM_DAYS = 90
TEAM_NAME = "FC Demo"
COACH_PASSWORD = "coach123"
ATHLETE_PASSWORD = "athlete123"

FIRST_NAMES = [
    "Alex", "Ben", "Carlos", "David", "Erik", "Finn", "George", "Hugo",
    "Ivan", "Jake", "Karl", "Liam", "Marco", "Noah", "Oscar", "Pedro",
    "Quinn", "Rafa", "Sam", "Tom", "Umar", "Victor", "Will", "Xavier", "Yusuf",
]
LAST_NAMES = [
    "Anderson", "Baker", "Costa", "Diaz", "Evans", "Fernandez", "Garcia",
    "Hansen", "Ibrahim", "Jensen", "Kim", "Lopez", "Martinez", "Nielsen",
    "Olsen", "Petersen", "Quinn", "Rodriguez", "Silva", "Torres", "Underwood",
    "Vega", "Williams", "Xu", "Young",
]

POSITIONS = [
    "GK", "CB", "CB", "LB", "RB",
    "CDM", "CDM", "CM", "CM", "CAM",
    "LW", "RW", "LW", "RW",
    "ST", "ST", "CF",
    "CB", "RB", "CM", "CM", "LW", "ST", "GK", "CDM",
]


def _build_periodized_load(day_index: int, base_load: float) -> float:
    """Build/recovery periodized load: 3 weeks build, 1 week recovery."""
    cycle_day = day_index % 28
    ramp = 0.8 + 0.4 * (cycle_day / 21) if cycle_day < 21 else 0.5

    # Day-of-week variation (Mon=hard, Wed=hard, Fri=match, Sat/Sun=rest)
    dow = (day_index % 7)
    day_mult = {0: 1.2, 1: 0.7, 2: 1.1, 3: 0.6, 4: 1.4, 5: 0.3, 6: 0.2}
    mult = day_mult.get(dow, 0.8)

    return base_load * ramp * mult * random.uniform(0.85, 1.15)


def _generate_athlete_metrics(
    athlete_id: uuid.UUID,
    start_date: date,
    anomaly_days: set[int],
    profile_seed: int,
) -> list[MetricRecord]:
    """Generate 90 days of metric records for one athlete."""
    rng = random.Random(profile_seed)
    records: list[MetricRecord] = []

    # Per-athlete baseline variation
    base_rhr = rng.uniform(50, 68)
    base_hrv = rng.uniform(40, 75)
    base_sleep = rng.uniform(390, 480)  # minutes
    base_load = rng.uniform(300, 600)  # arbitrary load units
    base_bb = rng.uniform(50, 80)  # body battery

    for day_offset in range(NUM_DAYS):
        d = start_date + timedelta(days=day_offset)
        ts = datetime(d.year, d.month, d.day, 7, 0, 0, tzinfo=UTC)
        is_anomaly = day_offset in anomaly_days

        # Resting heart rate
        rhr = base_rhr + rng.gauss(0, 2)
        if is_anomaly and rng.random() < 0.4:
            rhr += rng.choice([15, -15])  # spike or drop
        records.append(MetricRecord(
            athlete_id=athlete_id, metric_type="resting_hr",
            recorded_at=ts, value=round(rhr, 1), source="garmin",
        ))

        # HRV RMSSD
        hrv = base_hrv + rng.gauss(0, 5)
        if is_anomaly and rng.random() < 0.4:
            hrv -= rng.uniform(20, 30)  # sudden drop
        records.append(MetricRecord(
            athlete_id=athlete_id, metric_type="hrv_rmssd",
            recorded_at=ts + timedelta(minutes=1), value=round(max(10, hrv), 1),
            source="garmin",
        ))

        # Sleep duration
        sleep = base_sleep + rng.gauss(0, 20)
        if is_anomaly and rng.random() < 0.3:
            sleep -= rng.uniform(120, 180)  # poor night
        records.append(MetricRecord(
            athlete_id=athlete_id, metric_type="sleep_duration",
            recorded_at=ts + timedelta(minutes=2),
            value=round(max(120, sleep), 0), source="garmin",
        ))

        # Training load
        load = _build_periodized_load(day_offset, base_load)
        if is_anomaly and rng.random() < 0.3:
            load *= rng.uniform(2.0, 2.5)  # load spike
        records.append(MetricRecord(
            athlete_id=athlete_id, metric_type="training_load",
            recorded_at=ts + timedelta(minutes=3), value=round(max(0, load), 1),
            source="garmin",
        ))

        # Body battery
        bb = base_bb + rng.gauss(0, 5)
        # Body battery inversely related to load
        bb -= (load / base_load - 1) * 15
        if is_anomaly and rng.random() < 0.3:
            bb -= rng.uniform(20, 35)
        records.append(MetricRecord(
            athlete_id=athlete_id, metric_type="body_battery",
            recorded_at=ts + timedelta(minutes=4),
            value=round(max(5, min(100, bb)), 0), source="garmin",
        ))

    return records


def _generate_training_sessions(
    athlete_id: uuid.UUID,
    start_date: date,
) -> tuple[list[TrainingSession], list[SessionMetrics]]:
    """Generate training sessions for the 90-day period."""
    sessions: list[TrainingSession] = []
    metrics_list: list[SessionMetrics] = []

    for day_offset in range(NUM_DAYS):
        d = start_date + timedelta(days=day_offset)
        dow = day_offset % 7
        # Training days: Mon, Tue, Wed, Thu, Fri (some variation)
        if dow >= 5:
            continue  # weekend rest
        if random.random() < 0.1:
            continue  # occasional rest day

        session_type = "match" if dow == 4 else "training"
        duration = random.randint(70, 100) if session_type == "match" else random.randint(60, 90)
        source = random.choice(["garmin", "garmin", "garmin", "manual"])

        session_id = uuid.uuid4()
        started = datetime(d.year, d.month, d.day, 10, 0, 0, tzinfo=UTC)

        sessions.append(TrainingSession(
            id=session_id,
            athlete_id=athlete_id,
            session_type=session_type,
            start_time=started,
            end_time=started + timedelta(minutes=duration),
            duration_minutes=duration,
            source=source,
        ))

        # Session metrics
        avg_hr = random.randint(130, 165)
        metrics_list.append(SessionMetrics(
            session_id=session_id,
            hr_avg=float(avg_hr),
            hr_max=float(avg_hr + random.randint(15, 40)),
            energy_kcal=float(random.randint(400, 800)),
            distance_m=random.uniform(5000, 12000) if session_type == "match" else random.uniform(3000, 8000),
        ))

    return sessions, metrics_list


def _generate_wellness_entries(
    athlete_id: uuid.UUID,
    start_date: date,
) -> list[WellnessEntry]:
    """Generate daily wellness entries."""
    entries: list[WellnessEntry] = []
    for day_offset in range(NUM_DAYS):
        d = start_date + timedelta(days=day_offset)
        if random.random() < 0.1:
            continue  # occasionally skipped
        entries.append(WellnessEntry(
            athlete_id=athlete_id,
            date=d,
            sleep_quality=random.randint(3, 5),
            fatigue=random.randint(1, 5),
            soreness=random.randint(1, 4),
            mood=random.randint(3, 5),
            notes=None,
        ))
    return entries


async def seed_database(db_url: str | None = None) -> dict:  # type: ignore[type-arg]
    """Seed the database with demo data.

    Args:
        db_url: Database URL override. Uses settings.DATABASE_URL if None.

    Returns:
        Summary dict with counts of created entities.
    """
    url = db_url or settings.DATABASE_URL
    engine = create_async_engine(url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    start_date = date.today() - timedelta(days=NUM_DAYS)
    hashed_coach = hash_password(COACH_PASSWORD)
    hashed_athlete = hash_password(ATHLETE_PASSWORD)

    async with session_factory() as db:
        # Team
        team = Team(name=TEAM_NAME)
        db.add(team)
        await db.flush()

        # Coaches
        coaches: list[User] = []
        for i, name in enumerate(["Coach Morgan", "Coach Taylor"]):
            coach = User(
                email=f"coach{i + 1}@fcdemo.com",
                hashed_password=hashed_coach,
                role="coach",
                full_name=name,
                team_id=team.id,
                is_active=True,
            )
            db.add(coach)
            coaches.append(coach)
        await db.flush()

        # Athletes
        athletes: list[User] = []
        all_metric_records: list[MetricRecord] = []
        all_sessions: list[TrainingSession] = []
        all_session_metrics: list[SessionMetrics] = []
        all_wellness: list[WellnessEntry] = []

        for i in range(NUM_ATHLETES):
            athlete = User(
                email=f"{FIRST_NAMES[i].lower()}.{LAST_NAMES[i].lower()}@fcdemo.com",
                hashed_password=hashed_athlete,
                role="athlete",
                full_name=f"{FIRST_NAMES[i]} {LAST_NAMES[i]}",
                team_id=team.id,
                ow_user_id=f"ow-{uuid.uuid4().hex[:12]}",
                is_active=True,
            )
            db.add(athlete)
            await db.flush()
            athletes.append(athlete)

            # Athlete profile
            profile = AthleteProfile(
                user_id=athlete.id,
                position=POSITIONS[i],
                height_cm=random.randint(170, 195),
                weight_kg=round(random.uniform(65, 92), 1),
                date_of_birth=date(random.randint(1995, 2004), random.randint(1, 12), random.randint(1, 28)),
            )
            db.add(profile)

            # Anomaly days: 2-3 per athlete, spread out
            num_anomalies = random.randint(2, 3)
            anomaly_days = set(random.sample(range(20, NUM_DAYS - 5), num_anomalies))

            # Metric records
            metrics = _generate_athlete_metrics(
                athlete.id, start_date, anomaly_days, profile_seed=i * 1000,
            )
            all_metric_records.extend(metrics)

            # Training sessions
            sessions, session_metrics = _generate_training_sessions(athlete.id, start_date)
            all_sessions.extend(sessions)
            all_session_metrics.extend(session_metrics)

            # Wellness entries
            wellness = _generate_wellness_entries(athlete.id, start_date)
            all_wellness.extend(wellness)

        # Bulk add records — order matters for FK constraints
        db.add_all(all_sessions)
        await db.flush()  # Ensure training_sessions exist before session_metrics FK references

        db.add_all(all_session_metrics)
        db.add_all(all_metric_records)
        db.add_all(all_wellness)

        await db.commit()

    await engine.dispose()

    return {
        "team": TEAM_NAME,
        "coaches": len(coaches),
        "athletes": len(athletes),
        "metric_records": len(all_metric_records),
        "training_sessions": len(all_sessions),
        "session_metrics": len(all_session_metrics),
        "wellness_entries": len(all_wellness),
    }


async def _main() -> None:
    """Run the seed script."""
    print(f"Seeding database: {settings.DATABASE_URL}")  # noqa: T201
    result = await seed_database()
    print("Seed complete:")  # noqa: T201
    for key, val in result.items():
        print(f"  {key}: {val}")  # noqa: T201


if __name__ == "__main__":
    asyncio.run(_main())
