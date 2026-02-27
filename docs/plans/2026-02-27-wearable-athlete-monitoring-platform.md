---
task_list_id: plan-2026-02-27-wearable-athlete-monitoring-platform
---

# Implementation Plan: Wearable Athlete Monitoring Platform V1

## Overview

Build a self-hosted athlete monitoring platform that aggregates Garmin Venu 3 wearable data through Open Wearables middleware, computes sports science analytics (ACWR, HRV trends, training monotony/strain, anomaly detection), and presents insights through a coach web dashboard (React + TypeScript) and athlete mobile app (React Native / Expo). The platform targets football teams in V1 with a single-team model and descriptive analytics only (no ML prediction).

## Context

The platform fills a market gap identified in competitive analysis: Kitman Labs-style data integration and analytics at accessible (non-enterprise) pricing. Current solutions (Catapult ~$100K/year, STATSports, KINEXON) target elite clubs. Our approach uses Open Wearables (MIT-licensed, self-hosted) as the wearable data abstraction layer, avoiding months of direct Garmin API integration work.

Key constraints:
- Garmin Cloud API is push-based (webhooks), not on-demand -- Open Wearables handles this
- No raw accelerometer/GPS from Garmin API -- no PlayerLoad or sprint detection in V1
- Open Wearables is v0.3.0-beta (young project, APIs may change before 1.0)
- Single-team model simplifies auth and data isolation

Reference systems: Kitman Labs Intelligence Platform (integration layer vision), WHOOP (single recovery score simplification), STATSports Pro Score (composite metrics), Catapult AMS (dashboard widgets).

## Design Decision

**Approach**: Layered monorepo architecture with Open Wearables as external sibling container. Our backend (FastAPI) polls Open Wearables API for normalized data, computes derived analytics, and stores results in TimescaleDB hypertables. The backend exposes its own REST API consumed by both the React web dashboard and React Native mobile app.

**Why not consume Open Wearables directly from frontends**: Analytics computation (ACWR, anomaly detection) requires server-side processing with historical context. Centralizing data access through our backend enables caching, derived metric storage, team/athlete authorization, and decouples frontends from Open Wearables API changes.

**Why TimescaleDB over plain PostgreSQL**: Time-series queries (rolling windows, aggregations over date ranges) are the primary access pattern. TimescaleDB hypertables with continuous aggregates eliminate repeated computation of daily/weekly rollups. The `timescaledb` extension runs inside standard PostgreSQL, so no separate database engine is needed.

**Why React Native over Flutter**: Open Wearables has a Flutter SDK for Apple Health/Samsung Health, but V1 only targets Garmin (cloud API, no SDK needed). React Native with Expo allows sharing TypeScript tooling/types with the web dashboard. If Flutter SDK becomes needed for V2 (Apple Health), this decision can be revisited.

## Implementation Phases

### Phase 1: Project Scaffolding and Infrastructure

**Objective**: Establish the monorepo structure, Docker Compose configuration with Open Wearables as sibling service, and development tooling. After this phase, `docker compose up` starts all services and the FastAPI backend returns a health check response.

**Verification Approach**: Docker Compose starts all services without errors. The FastAPI backend responds on its configured port. PostgreSQL with TimescaleDB extension is accessible and the extension is loaded.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/test_health.py` -- health endpoint returns 200 with `{"status": "ok", "version": "0.1.0"}`
- [ ] Write test: `backend/tests/test_db_connection.py` -- database connection succeeds and TimescaleDB extension is available
- [ ] Create monorepo root structure:
  ```
  wearable/
  ├── backend/              # FastAPI application
  │   ├── app/
  │   │   ├── __init__.py
  │   │   ├── main.py       # FastAPI app factory
  │   │   ├── config.py     # Pydantic settings
  │   │   └── db.py         # SQLAlchemy + async engine
  │   ├── tests/
  │   ├── alembic/
  │   ├── alembic.ini
  │   ├── pyproject.toml     # uv/pip project config
  │   └── Dockerfile
  ├── web/                   # React + TypeScript dashboard
  │   ├── src/
  │   ├── package.json
  │   └── Dockerfile
  ├── mobile/                # React Native (Expo) app
  │   ├── src/
  │   └── package.json
  ├── docker-compose.yml     # All services including Open Wearables
  ├── docker-compose.dev.yml # Dev overrides (hot reload, volumes)
  ├── .env.example
  ├── Makefile
  └── docs/
      ├── plans/
      └── decisions/
  ```
- [ ] Create `docker-compose.yml` with services:
  - `db`: PostgreSQL 16 + TimescaleDB extension (port 5432)
  - `redis`: Redis 7 (port 6379)
  - `backend`: FastAPI app (port 8001)
  - `celery-worker`: Celery worker for async tasks
  - `celery-beat`: Celery beat for periodic tasks
  - Open Wearables services (cloned/referenced as git submodule or external compose): `ow-backend` (port 8000), `ow-db`, `ow-redis`, `ow-celery-worker`, `ow-celery-beat`
  - Shared Docker network `wearable-net` so our backend can reach `ow-backend:8000`
- [ ] Create `backend/app/config.py` using Pydantic `BaseSettings` with env vars: `DATABASE_URL`, `REDIS_URL`, `OW_API_URL`, `OW_API_KEY`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- [ ] Create `backend/app/db.py` with async SQLAlchemy engine and session factory
- [ ] Create `backend/app/main.py` with FastAPI app, health endpoint, CORS middleware
- [ ] Create Alembic configuration with initial migration enabling TimescaleDB extension (`CREATE EXTENSION IF NOT EXISTS timescaledb`)
- [ ] Create `Makefile` with targets: `up`, `down`, `test`, `migrate`, `seed`, `lint`
- [ ] Verify: `docker compose up` starts all services, `curl localhost:8001/health` returns 200

**Exit Conditions**:

Build Verification:
- [ ] `docker compose build` succeeds for all services
- [ ] `docker compose run backend ruff check app/` passes (linting)
- [ ] `docker compose run backend mypy app/` passes (type checking)

Runtime Verification:
- [ ] `docker compose up -d` starts all containers to healthy state
- [ ] Backend responds at `http://localhost:8001/health`
- [ ] Open Wearables responds at `http://localhost:8000/docs`
- [ ] PostgreSQL accepts connections and `SELECT * FROM pg_extension WHERE extname = 'timescaledb'` returns a row

Functional Verification:
- [ ] `docker compose run backend pytest tests/test_health.py` passes
- [ ] `docker compose run backend pytest tests/test_db_connection.py` passes

---

### Phase 2: Database Models and Migrations

**Objective**: Define all SQLAlchemy models for the platform's domain: teams, coaches, athletes, training sessions, wellness questionnaires, and time-series metrics. Create Alembic migrations. After this phase, the database schema is fully created with TimescaleDB hypertables for time-series data.

**Verification Approach**: All migrations apply cleanly. Model unit tests verify table creation, relationships, and constraints. TimescaleDB hypertables are confirmed for time-series tables.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/models/test_team_model.py` -- Team creation, field validation
- [ ] Write test: `backend/tests/models/test_user_models.py` -- Coach and Athlete creation, team FK, unique email constraint
- [ ] Write test: `backend/tests/models/test_session_models.py` -- TrainingSession creation (both garmin-sourced and manual), athlete FK, date range
- [ ] Write test: `backend/tests/models/test_wellness_model.py` -- WellnessEntry creation, sRPE/soreness/mood fields, athlete FK
- [ ] Write test: `backend/tests/models/test_metric_models.py` -- MetricRecord insertion into hypertable, timestamp ordering, athlete FK
- [ ] Implement model: `backend/app/models/team.py` -- `Team(id, name, sport, created_at)`
- [ ] Implement model: `backend/app/models/user.py` -- `User(id, email, hashed_password, role[coach|athlete], full_name, team_id, ow_user_id, created_at)`
- [ ] Implement model: `backend/app/models/athlete_profile.py` -- `AthleteProfile(id, user_id, date_of_birth, position, height_cm, weight_kg, garmin_connected, ow_connection_id)`
- [ ] Implement model: `backend/app/models/training_session.py` -- `TrainingSession(id, athlete_id, source[garmin|manual], session_type[match|training|gym|recovery], start_time, end_time, duration_minutes, ow_event_id, notes, created_by)`
- [ ] Implement model: `backend/app/models/session_metrics.py` -- `SessionMetrics(id, session_id, hr_avg, hr_max, hr_min, distance_m, energy_kcal, steps, max_speed_ms, elevation_gain_m)` -- one-to-one with TrainingSession
- [ ] Implement model: `backend/app/models/wellness_entry.py` -- `WellnessEntry(id, athlete_id, date, srpe, srpe_duration_min, soreness[1-10], fatigue[1-10], mood[1-5], sleep_quality[1-5], notes, created_at)`
- [ ] Implement model: `backend/app/models/metric_record.py` -- `MetricRecord(athlete_id, metric_type, value, recorded_at, source, ow_series_id)` -- TimescaleDB hypertable partitioned on `recorded_at`
- [ ] Implement model: `backend/app/models/__init__.py` -- barrel export of all models
- [ ] Create Alembic migration for all tables, including `SELECT create_hypertable('metric_records', 'recorded_at')` for the time-series table
- [ ] Verify: all migrations apply, all tests pass

**Exit Conditions**:

Build Verification:
- [ ] `docker compose run backend ruff check app/` passes
- [ ] `docker compose run backend mypy app/` passes
- [ ] `docker compose run backend alembic upgrade head` succeeds

Runtime Verification:
- [ ] All tables exist in PostgreSQL: `\dt` shows team, user, athlete_profile, training_session, session_metrics, wellness_entry, metric_record
- [ ] `metric_records` is a TimescaleDB hypertable: `SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'metric_records'` returns a row
- [ ] Foreign key constraints are enforced (attempt invalid FK insert fails)

Functional Verification:
- [ ] `docker compose run backend pytest tests/models/` passes (all model tests)
- [ ] Alembic `downgrade` and re-`upgrade` succeeds cleanly (migration reversibility)

---

### Phase 3: Authentication and Authorization

**Objective**: Implement custom JWT authentication with role-based access control (coach vs. athlete). Coaches can access all team data; athletes can access only their own data. After this phase, protected endpoints require valid JWT tokens and enforce role permissions.

**Verification Approach**: Unit tests verify JWT creation/validation, password hashing, and role-based access control. Integration tests verify the full login flow and protected endpoint access.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/auth/test_password.py` -- hash creation, hash verification, rejection of wrong password (Argon2)
- [ ] Write test: `backend/tests/auth/test_jwt.py` -- token creation with claims (sub, role, team_id, exp), token decode, expired token rejection, invalid token rejection
- [ ] Write test: `backend/tests/auth/test_dependencies.py` -- `get_current_user` extracts user from valid token, rejects expired/invalid, `require_coach` allows coach role and rejects athlete role
- [ ] Write test: `backend/tests/auth/test_login_endpoint.py` -- POST `/api/v1/auth/login` returns access + refresh tokens for valid credentials, 401 for invalid, 401 for nonexistent user
- [ ] Write test: `backend/tests/auth/test_register_endpoint.py` -- POST `/api/v1/auth/register` creates user, rejects duplicate email, validates required fields
- [ ] Write test: `backend/tests/auth/test_refresh_endpoint.py` -- POST `/api/v1/auth/refresh` issues new access token from valid refresh token
- [ ] Implement: `backend/app/auth/password.py` -- `hash_password(plain) -> str`, `verify_password(plain, hashed) -> bool` using `pwdlib[argon2]`
- [ ] Implement: `backend/app/auth/jwt.py` -- `create_access_token(user_id, role, team_id) -> str`, `create_refresh_token(user_id) -> str`, `decode_token(token) -> TokenPayload` using `PyJWT`
- [ ] Implement: `backend/app/auth/dependencies.py` -- FastAPI dependencies: `get_current_user`, `require_coach`, `require_athlete`, `require_team_member`
- [ ] Implement: `backend/app/auth/schemas.py` -- Pydantic schemas: `LoginRequest`, `TokenResponse`, `RegisterRequest`, `TokenPayload`
- [ ] Implement: `backend/app/auth/router.py` -- `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/refresh`, `/api/v1/auth/me`
- [ ] Implement: `backend/app/auth/__init__.py` -- barrel export
- [ ] Register auth router in `backend/app/main.py`
- [ ] Verify: all auth tests pass, manual login via curl returns JWT

**Exit Conditions**:

Build Verification:
- [ ] `docker compose run backend ruff check app/` passes
- [ ] `docker compose run backend mypy app/` passes

Runtime Verification:
- [ ] Backend starts with auth routes registered (visible in `/docs` Swagger UI)
- [ ] `POST /api/v1/auth/register` with valid payload returns 201
- [ ] `POST /api/v1/auth/login` with registered credentials returns JWT tokens
- [ ] `GET /api/v1/auth/me` with valid Bearer token returns user info

Functional Verification:
- [ ] `docker compose run backend pytest tests/auth/` passes (all auth tests)
- [ ] Protected endpoint returns 401 without token
- [ ] Protected endpoint returns 403 when athlete accesses coach-only route

---

### Phase 4: Open Wearables Integration Service

**Objective**: Build the service layer that communicates with Open Wearables API to sync athlete data. This includes user provisioning in OW, Garmin connection status tracking, and data polling for time-series, workouts, and sleep. After this phase, the backend can create OW users, check Garmin connection status, and fetch normalized health data.

**Verification Approach**: Unit tests use mocked HTTP responses to verify OW client behavior. Integration tests (marked separately) verify actual OW API communication in Docker environment.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/services/test_ow_client.py` -- OW API client: create user, list users, get user connections, get timeseries (mock HTTP responses with `httpx` respx or `respx` library)
- [ ] Write test: `backend/tests/services/test_ow_sync_service.py` -- sync service: maps OW workout to TrainingSession, maps OW sleep to relevant metric records, maps OW timeseries to MetricRecord rows, handles pagination, deduplicates by `ow_event_id`/`ow_series_id`
- [ ] Write test: `backend/tests/services/test_ow_user_service.py` -- user provisioning: creates OW user on athlete registration, stores `ow_user_id` on local user, retrieves Garmin connection status
- [ ] Implement: `backend/app/services/ow_client.py` -- async HTTP client wrapping Open Wearables REST API:
  - `create_user(email, first_name, last_name) -> OWUser`
  - `get_user(ow_user_id) -> OWUser`
  - `get_user_connections(ow_user_id) -> list[OWConnection]`
  - `get_timeseries(ow_user_id, types, start, end, resolution) -> list[OWDataPoint]`
  - `get_workouts(ow_user_id, start, end) -> list[OWWorkout]`
  - `get_sleep(ow_user_id, start, end) -> list[OWSleep]`
  - Uses `httpx.AsyncClient` with `X-Open-Wearables-API-Key` header
  - Handles cursor-based pagination automatically
- [ ] Implement: `backend/app/services/ow_schemas.py` -- Pydantic models for OW API responses: `OWUser`, `OWConnection`, `OWDataPoint`, `OWWorkout`, `OWSleep`, `OWWorkoutDetails`, `OWSleepDetails`
- [ ] Implement: `backend/app/services/ow_user_service.py` -- orchestrates OW user lifecycle:
  - `provision_ow_user(athlete_user) -> str` (returns ow_user_id)
  - `get_garmin_connection_status(athlete_user) -> ConnectionStatus`
  - `get_garmin_connect_url(athlete_user) -> str` (OAuth initiation URL for mobile app)
- [ ] Implement: `backend/app/services/ow_sync_service.py` -- data synchronization:
  - `sync_athlete_timeseries(athlete, start, end) -> SyncResult`
  - `sync_athlete_workouts(athlete, start, end) -> SyncResult`
  - `sync_athlete_sleep(athlete, start, end) -> SyncResult`
  - `sync_all_athletes(team_id, start, end) -> list[SyncResult]`
  - Maps OW data types to our MetricRecord types
  - Deduplicates using `ow_event_id` and `ow_series_id`
- [ ] Implement: `backend/app/services/ow_mapper.py` -- data transformation helpers:
  - `map_ow_workout_to_session(ow_workout, athlete_id) -> TrainingSession + SessionMetrics`
  - `map_ow_timeseries_to_records(ow_data, athlete_id) -> list[MetricRecord]`
  - `map_ow_sleep_to_records(ow_sleep, athlete_id) -> list[MetricRecord]`
- [ ] Verify: all OW service tests pass with mocked responses

**Exit Conditions**:

Build Verification:
- [ ] `docker compose run backend ruff check app/` passes
- [ ] `docker compose run backend mypy app/` passes

Runtime Verification:
- [ ] Backend starts without import errors for new modules
- [ ] OW client can reach `ow-backend:8000` from within Docker network (connectivity test)
- [ ] `docker compose run backend python -c "from app.services.ow_client import OWClient; print('OK')"` succeeds

Functional Verification:
- [ ] `docker compose run backend pytest tests/services/` passes (all service tests with mocks)
- [ ] Integration smoke test: create OW user via client, verify user exists in OW system (requires OW services running)

---

### Phase 5: Data Sync Celery Tasks and Scheduling

**Objective**: Implement Celery tasks for periodic and on-demand data synchronization from Open Wearables. After this phase, Celery beat triggers hourly syncs for all athletes, and manual sync can be triggered via API endpoint.

**Verification Approach**: Unit tests verify task logic with mocked services. Integration tests verify Celery task execution and scheduling.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/tasks/test_sync_tasks.py` -- `sync_athlete_data_task` calls sync service with correct parameters, handles sync errors gracefully, records sync status
- [ ] Write test: `backend/tests/tasks/test_sync_all_task.py` -- `sync_all_athletes_task` fetches all athletes with Garmin connected, dispatches individual sync tasks
- [ ] Write test: `backend/tests/api/test_sync_endpoints.py` -- POST `/api/v1/sync/athlete/{id}` triggers manual sync (coach only), GET `/api/v1/sync/status` returns last sync timestamps
- [ ] Implement: `backend/app/tasks/__init__.py` -- Celery app configuration
- [ ] Implement: `backend/app/tasks/celery_app.py` -- Celery app factory with Redis broker, task autodiscovery
- [ ] Implement: `backend/app/tasks/sync_tasks.py`:
  - `sync_athlete_data_task(athlete_id, start_date, end_date)` -- syncs timeseries + workouts + sleep for one athlete
  - `sync_all_athletes_task()` -- discovers all Garmin-connected athletes, fans out individual sync tasks
  - Error handling with retry (max 3 retries, exponential backoff)
  - Sync status tracking in Redis (last_sync_at, sync_status, error_message per athlete)
- [ ] Implement: `backend/app/tasks/schedule.py` -- Celery beat schedule:
  - `sync_all_athletes_task` every 60 minutes
  - Configurable via `SYNC_INTERVAL_MINUTES` env var
- [ ] Implement: `backend/app/api/sync_router.py`:
  - `POST /api/v1/sync/athlete/{athlete_id}` -- trigger manual sync (coach only)
  - `POST /api/v1/sync/team` -- trigger full team sync (coach only)
  - `GET /api/v1/sync/status` -- return sync status for all athletes
- [ ] Register sync router in `backend/app/main.py`
- [ ] Verify: Celery worker processes tasks, beat schedule triggers on time

**Exit Conditions**:

Build Verification:
- [ ] `docker compose run backend ruff check app/` passes
- [ ] `docker compose run backend mypy app/` passes

Runtime Verification:
- [ ] `docker compose up celery-worker celery-beat` starts without errors
- [ ] Celery worker connects to Redis broker (visible in logs)
- [ ] Celery beat schedules `sync_all_athletes_task` (visible in beat logs)
- [ ] Flower dashboard at `localhost:5555` shows registered tasks

Functional Verification:
- [ ] `docker compose run backend pytest tests/tasks/` passes
- [ ] `docker compose run backend pytest tests/api/test_sync_endpoints.py` passes
- [ ] Manual sync via `POST /api/v1/sync/athlete/{id}` returns 202 and task appears in Celery

---

### Phase 6: Athlete and Team Management API

**Objective**: Build CRUD endpoints for team, athlete, and coach management. Coaches can manage the team roster. Athletes can view/update their own profile. After this phase, the full user management API is functional.

**Verification Approach**: Integration tests verify all CRUD operations, authorization rules, and data validation.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/api/test_team_endpoints.py` -- GET/PUT team info (coach only), team creation during initial setup
- [ ] Write test: `backend/tests/api/test_athlete_endpoints.py` -- CRUD athletes: list (coach), get (coach + self), create (coach), update (coach + self for profile fields), delete/deactivate (coach)
- [ ] Write test: `backend/tests/api/test_coach_endpoints.py` -- invite coach, list coaches
- [ ] Write test: `backend/tests/api/test_athlete_profile_endpoints.py` -- athlete updates own profile (position, height, weight), coach views all profiles
- [ ] Implement: `backend/app/api/schemas/team.py` -- `TeamResponse`, `TeamUpdateRequest`
- [ ] Implement: `backend/app/api/schemas/athlete.py` -- `AthleteListResponse`, `AthleteDetailResponse`, `AthleteCreateRequest`, `AthleteUpdateRequest`, `AthleteProfileResponse`
- [ ] Implement: `backend/app/api/schemas/coach.py` -- `CoachResponse`, `CoachInviteRequest`
- [ ] Implement: `backend/app/repositories/team_repo.py` -- database queries for team operations
- [ ] Implement: `backend/app/repositories/user_repo.py` -- database queries for user CRUD
- [ ] Implement: `backend/app/api/team_router.py` -- `/api/v1/team` endpoints
- [ ] Implement: `backend/app/api/athlete_router.py` -- `/api/v1/athletes` endpoints
- [ ] Implement: `backend/app/api/coach_router.py` -- `/api/v1/coaches` endpoints
- [ ] Register all routers in `backend/app/main.py`
- [ ] Verify: all management API tests pass

**Exit Conditions**:

Build Verification:
- [ ] `docker compose run backend ruff check app/` passes
- [ ] `docker compose run backend mypy app/` passes

Runtime Verification:
- [ ] All new endpoints visible in Swagger UI at `/docs`
- [ ] Backend starts without errors

Functional Verification:
- [ ] `docker compose run backend pytest tests/api/test_team_endpoints.py` passes
- [ ] `docker compose run backend pytest tests/api/test_athlete_endpoints.py` passes
- [ ] `docker compose run backend pytest tests/api/test_coach_endpoints.py` passes
- [ ] `docker compose run backend pytest tests/api/test_athlete_profile_endpoints.py` passes
- [ ] Coach can create athlete, athlete can view own profile, athlete cannot view other athletes' profiles

---

### Phase 7: Training Session and Wellness API

**Objective**: Build endpoints for manual training session logging (by coaches) and wellness questionnaire submission (by athletes). These complement Garmin-sourced sessions. After this phase, coaches can log sessions and athletes can submit daily wellness data.

**Verification Approach**: Tests verify session creation (manual vs. garmin source), wellness entry validation (field ranges), and proper authorization.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/api/test_session_endpoints.py` -- create manual session (coach), list sessions for athlete (coach + self), get session detail, filter by date range and type, session with metrics
- [ ] Write test: `backend/tests/api/test_wellness_endpoints.py` -- submit wellness entry (athlete, one per day), update today's entry, get wellness history for athlete (coach + self), field validation (sRPE 1-10, soreness 1-10, mood 1-5)
- [ ] Write test: `backend/tests/services/test_session_service.py` -- session creation, session listing with filters, compute session load (sRPE x duration)
- [ ] Write test: `backend/tests/services/test_wellness_service.py` -- wellness entry creation, duplicate date prevention, wellness history retrieval
- [ ] Implement: `backend/app/api/schemas/session.py` -- `SessionCreateRequest`, `SessionResponse`, `SessionListResponse`, `SessionMetricsResponse`, `SessionFilterParams`
- [ ] Implement: `backend/app/api/schemas/wellness.py` -- `WellnessCreateRequest`, `WellnessResponse`, `WellnessHistoryResponse`
- [ ] Implement: `backend/app/services/session_service.py` -- business logic for training sessions:
  - `create_manual_session(data, coach_id) -> TrainingSession`
  - `list_sessions(athlete_id, filters) -> list[TrainingSession]`
  - `get_session_detail(session_id) -> TrainingSession + SessionMetrics`
  - `compute_session_load(session) -> float` (sRPE x duration_minutes)
- [ ] Implement: `backend/app/services/wellness_service.py` -- business logic for wellness:
  - `submit_wellness(athlete_id, data) -> WellnessEntry`
  - `get_wellness_history(athlete_id, start, end) -> list[WellnessEntry]`
  - `get_latest_wellness(athlete_id) -> WellnessEntry | None`
- [ ] Implement: `backend/app/repositories/session_repo.py` -- session database queries
- [ ] Implement: `backend/app/repositories/wellness_repo.py` -- wellness database queries
- [ ] Implement: `backend/app/api/session_router.py` -- `/api/v1/sessions` endpoints
- [ ] Implement: `backend/app/api/wellness_router.py` -- `/api/v1/wellness` endpoints
- [ ] Register routers in `backend/app/main.py`
- [ ] Verify: all session and wellness tests pass

**Exit Conditions**:

Build Verification:
- [ ] `docker compose run backend ruff check app/` passes
- [ ] `docker compose run backend mypy app/` passes

Runtime Verification:
- [ ] Session and wellness endpoints visible in Swagger UI
- [ ] Backend starts without errors

Functional Verification:
- [ ] `docker compose run backend pytest tests/api/test_session_endpoints.py` passes
- [ ] `docker compose run backend pytest tests/api/test_wellness_endpoints.py` passes
- [ ] `docker compose run backend pytest tests/services/test_session_service.py` passes
- [ ] `docker compose run backend pytest tests/services/test_wellness_service.py` passes
- [ ] Manual session with sRPE load computes correctly (sRPE x duration)
- [ ] Duplicate wellness entry for same date is rejected with 409

---

### Phase 8: Analytics Engine -- ACWR and Training Load

**Objective**: Implement the core sports science calculations: ACWR using EWMA method, training monotony, and training strain. These are computed from session load data (both Garmin-derived and manual sRPE). After this phase, the backend can compute and serve ACWR, monotony, and strain for any athlete over any date range.

**Verification Approach**: Unit tests verify calculations against known sports science reference values. Tests use deterministic input data with hand-calculated expected outputs.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/analytics/test_ewma.py` -- EWMA calculation with known inputs:
  - Decay constant calculation: gamma_a = 2/(N+1) for N=7 (acute) and N=28 (chronic)
  - EWMA_today = Load_today x gamma + (1 - gamma) x EWMA_yesterday
  - Edge case: first day (no prior EWMA), missing days (zero load), single data point
- [ ] Write test: `backend/tests/analytics/test_acwr.py` -- ACWR = acute_ewma / chronic_ewma:
  - Sweet spot: ACWR between 0.8-1.3 returns "optimal" zone
  - Danger zone: ACWR > 1.5 returns "high_risk"
  - Undertraining: ACWR < 0.8 returns "undertraining"
  - Edge case: chronic_ewma near zero (early training history)
  - Known reference dataset: 28 days of loads -> expected ACWR value within 0.01 tolerance
- [ ] Write test: `backend/tests/analytics/test_monotony.py` -- monotony = mean_daily_load / std_daily_load:
  - 7-day window with known loads
  - Edge case: all same loads (std=0, return infinity/flag)
  - Edge case: single day of data
- [ ] Write test: `backend/tests/analytics/test_strain.py` -- strain = weekly_load x monotony:
  - Known 7-day loads -> expected strain value
- [ ] Write test: `backend/tests/analytics/test_training_load_service.py` -- integration: service fetches session loads from DB, computes ACWR/monotony/strain, returns structured response
- [ ] Implement: `backend/app/analytics/ewma.py` -- pure function:
  - `compute_ewma(loads: list[float], decay_days: int) -> list[float]`
  - `compute_ewma_single(load_today: float, ewma_yesterday: float, decay_days: int) -> float`
- [ ] Implement: `backend/app/analytics/acwr.py` -- pure functions:
  - `compute_acwr(daily_loads: list[DailyLoad], acute_days=7, chronic_days=28) -> ACWRResult`
  - `classify_acwr_zone(acwr_value: float) -> ACWRZone` (enum: undertraining, optimal, caution, high_risk)
  - `ACWRResult(acute_ewma, chronic_ewma, acwr_value, zone, date)`
- [ ] Implement: `backend/app/analytics/monotony.py` -- pure functions:
  - `compute_monotony(daily_loads: list[float], window_days=7) -> float`
  - `compute_strain(weekly_total_load: float, monotony: float) -> float`
- [ ] Implement: `backend/app/analytics/load_helpers.py` -- helpers:
  - `compute_session_load(session: TrainingSession, wellness: WellnessEntry | None) -> float` (sRPE x duration for manual; HR-based TRIMP for Garmin sessions)
  - `aggregate_daily_loads(sessions: list, start: date, end: date) -> list[DailyLoad]` (fills missing days with zero)
  - `DailyLoad(date, total_load, session_count)`
- [ ] Implement: `backend/app/services/training_load_service.py`:
  - `get_acwr(athlete_id, as_of_date) -> ACWRResult`
  - `get_training_load_summary(athlete_id, start, end) -> TrainingLoadSummary` (includes ACWR, monotony, strain, daily loads)
  - `get_team_acwr_overview(team_id, as_of_date) -> list[AthleteACWR]`
- [ ] Implement: `backend/app/api/schemas/analytics.py` -- response schemas for analytics data
- [ ] Implement: `backend/app/api/analytics_router.py`:
  - `GET /api/v1/analytics/athlete/{id}/acwr` -- ACWR with history
  - `GET /api/v1/analytics/athlete/{id}/training-load` -- full training load summary
  - `GET /api/v1/analytics/team/acwr-overview` -- team ACWR overview for coach
- [ ] Register analytics router in `backend/app/main.py`
- [ ] Verify: all analytics tests pass with reference values

**Exit Conditions**:

Build Verification:
- [ ] `docker compose run backend ruff check app/` passes
- [ ] `docker compose run backend mypy app/` passes

Runtime Verification:
- [ ] Analytics endpoints visible in Swagger UI
- [ ] Backend starts without errors

Functional Verification:
- [ ] `docker compose run backend pytest tests/analytics/` passes (all pure function tests)
- [ ] `docker compose run backend pytest tests/services/test_training_load_service.py` passes
- [ ] `docker compose run backend pytest tests/api/test_analytics_router.py` passes (if created)
- [ ] ACWR computation for 28-day reference dataset matches expected value within 0.01 tolerance
- [ ] Monotony computation for 7-day reference dataset matches expected value within 0.01 tolerance
- [ ] ACWR zone classification is correct: 0.7 -> undertraining, 1.0 -> optimal, 1.4 -> caution, 2.1 -> high_risk

---

### Phase 9: Analytics Engine -- HRV, Sleep, and Recovery

**Objective**: Implement HRV trend analysis (RMSSD rolling mean + CV), sleep quality tracking, and a composite recovery score (inspired by WHOOP). After this phase, the backend can compute HRV trends, sleep summaries, and a daily readiness/recovery score.

**Verification Approach**: Unit tests verify HRV rolling statistics, sleep aggregation, and recovery score formula against deterministic inputs.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/analytics/test_hrv.py`:
  - 7-day rolling mean of RMSSD values
  - 7-day rolling CV (coefficient of variation = std/mean)
  - Trend detection: improving (mean increasing, CV stable/decreasing), declining (mean decreasing or CV increasing), stable
  - Edge case: fewer than 7 days of data, missing days
- [ ] Write test: `backend/tests/analytics/test_sleep.py`:
  - Sleep duration aggregation from MetricRecord
  - Sleep stage breakdown (deep, REM, light, awake minutes)
  - Sleep efficiency calculation (sleep_time / time_in_bed)
  - 7-day sleep average
- [ ] Write test: `backend/tests/analytics/test_recovery_score.py`:
  - Composite score (0-100) weighted formula:
    - HRV component (40%): current RMSSD vs personal 30-day baseline
    - Sleep component (30%): last night sleep quality + duration vs target
    - Training load component (20%): inverse ACWR deviation from 1.0
    - Subjective component (10%): latest wellness questionnaire
  - Edge case: missing HRV data (use available components, re-weight)
  - Known inputs -> expected score within 1 point tolerance
- [ ] Implement: `backend/app/analytics/hrv.py` -- pure functions:
  - `compute_hrv_rolling_stats(rmssd_values: list[DailyHRV], window=7) -> HRVStats`
  - `classify_hrv_trend(stats: HRVStats) -> HRVTrend` (improving, stable, declining)
  - `HRVStats(rolling_mean, rolling_cv, trend, baseline_mean)`
- [ ] Implement: `backend/app/analytics/sleep.py` -- pure functions:
  - `compute_sleep_summary(sleep_records: list, date: date) -> SleepSummary`
  - `compute_sleep_average(summaries: list[SleepSummary], days=7) -> SleepAverage`
  - `SleepSummary(date, total_minutes, deep_minutes, rem_minutes, light_minutes, awake_minutes, efficiency)`
- [ ] Implement: `backend/app/analytics/recovery_score.py` -- pure function:
  - `compute_recovery_score(hrv_stats, sleep_summary, acwr_result, wellness_entry) -> RecoveryScore`
  - `RecoveryScore(total_score, hrv_component, sleep_component, load_component, subjective_component, available_components)`
- [ ] Implement: `backend/app/services/recovery_service.py`:
  - `get_hrv_analysis(athlete_id, start, end) -> HRVAnalysis`
  - `get_sleep_analysis(athlete_id, start, end) -> SleepAnalysis`
  - `get_recovery_score(athlete_id, date) -> RecoveryScore`
  - `get_team_recovery_overview(team_id, date) -> list[AthleteRecovery]`
- [ ] Add endpoints to `backend/app/api/analytics_router.py`:
  - `GET /api/v1/analytics/athlete/{id}/hrv`
  - `GET /api/v1/analytics/athlete/{id}/sleep`
  - `GET /api/v1/analytics/athlete/{id}/recovery`
  - `GET /api/v1/analytics/team/recovery-overview`
- [ ] Verify: all HRV/sleep/recovery tests pass

**Exit Conditions**:

Build Verification:
- [ ] `docker compose run backend ruff check app/` passes
- [ ] `docker compose run backend mypy app/` passes

Runtime Verification:
- [ ] New analytics endpoints visible in Swagger UI
- [ ] Backend starts without errors

Functional Verification:
- [ ] `docker compose run backend pytest tests/analytics/test_hrv.py` passes
- [ ] `docker compose run backend pytest tests/analytics/test_sleep.py` passes
- [ ] `docker compose run backend pytest tests/analytics/test_recovery_score.py` passes
- [ ] `docker compose run backend pytest tests/services/test_recovery_service.py` passes
- [ ] HRV rolling stats for 14-day reference dataset match expected values
- [ ] Recovery score for known inputs produces score within 1 point of expected value
- [ ] Recovery score gracefully handles missing HRV data (re-weighted score)

---

### Phase 10: Anomaly Detection Engine

**Objective**: Implement anomaly detection at per-metric and per-athlete levels using modified z-score on rolling windows. Detect unusual readings (e.g., sudden HRV drop, abnormally high resting HR, unusual training load spikes). After this phase, the system flags anomalies and provides explanations.

**Verification Approach**: Unit tests verify anomaly detection with synthetic datasets containing known anomalies at specific positions. Both per-metric (single metric unusual for this athlete) and per-athlete (this athlete unusual compared to team) levels are tested.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/analytics/test_anomaly_detection.py`:
  - Per-metric: modified z-score on 30-day rolling window detects value > 2.5 MAD from median
  - Per-athlete: athlete's metric deviates significantly from team distribution
  - Synthetic dataset with planted anomaly at day 15 (sudden HRV drop) -> detected
  - Synthetic dataset with no anomalies -> no false positives
  - Multiple simultaneous anomalies for one athlete -> all detected
  - Edge case: insufficient history (< 14 days) -> no anomaly flagged (need baseline)
- [ ] Write test: `backend/tests/analytics/test_anomaly_classifier.py`:
  - Anomaly severity: low (2.5-3.0 MAD), medium (3.0-4.0 MAD), high (> 4.0 MAD)
  - Anomaly type classification: spike, drop, trend_break
  - Anomaly explanation generation (human-readable string)
- [ ] Write test: `backend/tests/services/test_anomaly_service.py`:
  - Service fetches recent metric data, runs detection, returns anomalies
  - Team-level scan returns anomalies across all athletes
  - Anomaly history retrieval for an athlete
- [ ] Implement: `backend/app/analytics/anomaly_detection.py` -- pure functions:
  - `detect_metric_anomalies(values: list[DatedValue], window_days=30, threshold_mad=2.5) -> list[Anomaly]`
  - `detect_athlete_anomaly_vs_team(athlete_value: float, team_values: list[float], threshold_mad=2.5) -> Anomaly | None`
  - Uses modified z-score: `0.6745 * (x - median) / MAD` where MAD = median absolute deviation
- [ ] Implement: `backend/app/analytics/anomaly_classifier.py`:
  - `classify_severity(mad_score: float) -> AnomalySeverity` (low, medium, high)
  - `classify_type(current: float, median: float, trend: list[float]) -> AnomalyType` (spike, drop, trend_break)
  - `generate_explanation(anomaly: Anomaly, metric_type: str, athlete_name: str) -> str`
- [ ] Implement: `backend/app/analytics/anomaly_types.py` -- data classes:
  - `Anomaly(athlete_id, metric_type, value, expected_median, mad_score, severity, anomaly_type, explanation, detected_at)`
  - `AnomalySeverity` enum, `AnomalyType` enum
- [ ] Implement: `backend/app/services/anomaly_service.py`:
  - `scan_athlete_anomalies(athlete_id, date) -> list[Anomaly]` (per-metric)
  - `scan_team_anomalies(team_id, date) -> list[Anomaly]` (per-athlete comparison)
  - `get_anomaly_history(athlete_id, start, end) -> list[Anomaly]`
  - Scans metrics: resting_hr, hrv_rmssd, sleep_duration, training_load, body_battery
- [ ] Implement: `backend/app/models/anomaly_record.py` -- persist detected anomalies in DB
- [ ] Create Alembic migration for `anomaly_records` table
- [ ] Add endpoints to `backend/app/api/analytics_router.py`:
  - `GET /api/v1/analytics/athlete/{id}/anomalies` -- anomalies for one athlete
  - `GET /api/v1/analytics/team/anomalies` -- team-wide anomaly scan
- [ ] Implement: `backend/app/tasks/anomaly_tasks.py` -- Celery task for daily anomaly scan after sync completes
- [ ] Verify: all anomaly detection tests pass

**Exit Conditions**:

Build Verification:
- [ ] `docker compose run backend ruff check app/` passes
- [ ] `docker compose run backend mypy app/` passes
- [ ] `docker compose run backend alembic upgrade head` succeeds (new migration)

Runtime Verification:
- [ ] Anomaly endpoints visible in Swagger UI
- [ ] Anomaly scan Celery task registered (visible in Flower)
- [ ] Backend starts without errors

Functional Verification:
- [ ] `docker compose run backend pytest tests/analytics/test_anomaly_detection.py` passes
- [ ] `docker compose run backend pytest tests/analytics/test_anomaly_classifier.py` passes
- [ ] `docker compose run backend pytest tests/services/test_anomaly_service.py` passes
- [ ] Planted anomaly at day 15 in synthetic dataset is detected with correct severity
- [ ] No false positives on clean synthetic dataset
- [ ] Per-athlete anomaly correctly flags outlier vs team distribution

---

### Phase 11: TimescaleDB Continuous Aggregates and Query Optimization

**Objective**: Create TimescaleDB continuous aggregates for daily and weekly metric rollups. Optimize common query patterns (athlete dashboard, team overview) with materialized views. After this phase, dashboard queries execute in < 100ms for typical data volumes.

**Verification Approach**: Tests verify that continuous aggregates produce correct rollup values and that query performance meets targets.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/db/test_continuous_aggregates.py`:
  - Daily aggregate for resting_hr matches manual AVG/MIN/MAX over same period
  - Weekly aggregate for training_load matches manual SUM over same period
  - Aggregate refreshes pick up newly inserted data
  - Query against aggregate returns same results as raw query (correctness)
- [ ] Write test: `backend/tests/db/test_query_performance.py`:
  - Seed 90 days of data for 25 athletes (simulated team)
  - Team ACWR overview query executes in < 200ms
  - Individual athlete 30-day timeseries query executes in < 100ms
  - Team anomaly scan query executes in < 500ms
- [ ] Create Alembic migration for continuous aggregates:
  ```sql
  -- Daily metric rollup
  CREATE MATERIALIZED VIEW daily_metric_agg
  WITH (timescaledb.continuous) AS
  SELECT athlete_id, metric_type,
         time_bucket('1 day', recorded_at) AS bucket,
         AVG(value) AS avg_value,
         MIN(value) AS min_value,
         MAX(value) AS max_value,
         COUNT(*) AS sample_count
  FROM metric_records
  GROUP BY athlete_id, metric_type, bucket;

  -- Weekly training load rollup
  CREATE MATERIALIZED VIEW weekly_load_agg
  WITH (timescaledb.continuous) AS
  SELECT athlete_id,
         time_bucket('1 week', recorded_at) AS bucket,
         SUM(value) AS total_load,
         AVG(value) AS avg_daily_load,
         COUNT(*) AS session_count
  FROM metric_records
  WHERE metric_type = 'training_load'
  GROUP BY athlete_id, bucket;
  ```
- [ ] Implement refresh policies: `SELECT add_continuous_aggregate_policy(...)` with 1-hour lag
- [ ] Implement: `backend/app/repositories/metric_agg_repo.py` -- query functions using continuous aggregates:
  - `get_daily_metrics(athlete_id, metric_type, start, end) -> list[DailyMetric]`
  - `get_weekly_loads(athlete_id, start, end) -> list[WeeklyLoad]`
  - `get_team_latest_metrics(team_id, metric_type) -> list[AthleteMetric]`
- [ ] Update existing services to use aggregate repos where appropriate (read path optimization)
- [ ] Add database indexes: composite index on `(athlete_id, metric_type, recorded_at)` for metric_records
- [ ] Implement: `backend/app/db/seed.py` -- seed script generating 90 days of realistic data for 25 athletes (for performance testing)
- [ ] Verify: aggregates are correct, performance targets met

**Exit Conditions**:

Build Verification:
- [ ] `docker compose run backend ruff check app/` passes
- [ ] `docker compose run backend mypy app/` passes
- [ ] `docker compose run backend alembic upgrade head` succeeds (new migration)

Runtime Verification:
- [ ] Continuous aggregates exist: `SELECT * FROM timescaledb_information.continuous_aggregates` returns both views
- [ ] Refresh policies are active: `SELECT * FROM timescaledb_information.jobs` shows refresh jobs
- [ ] Backend starts without errors

Functional Verification:
- [ ] `docker compose run backend pytest tests/db/test_continuous_aggregates.py` passes
- [ ] `docker compose run backend pytest tests/db/test_query_performance.py` passes
- [ ] Daily aggregate AVG matches manual calculation for resting_hr
- [ ] Team overview query for 25 athletes x 90 days completes in < 200ms

---

### Phase 12: Web Dashboard -- Project Setup and Authentication

**Objective**: Scaffold the React + TypeScript web dashboard with Vite, configure routing (TanStack Router or React Router), implement login/auth flow, and establish the component architecture. After this phase, coaches can log in and see a basic authenticated shell.

**Verification Approach**: Component tests verify auth flow, route protection, and basic rendering. E2E tests verify full login flow against backend.

**Tasks** (tests first, then implementation):

- [ ] Write test: `web/src/__tests__/auth/LoginForm.test.tsx` -- form renders, validates inputs, submits credentials, handles error state
- [ ] Write test: `web/src/__tests__/auth/AuthProvider.test.tsx` -- stores JWT in memory (not localStorage for security), provides user context, redirects to login when unauthenticated
- [ ] Write test: `web/src/__tests__/auth/ProtectedRoute.test.tsx` -- renders children when authenticated, redirects when not
- [ ] Write test: `web/src/__tests__/api/apiClient.test.ts` -- attaches Bearer token to requests, handles 401 by redirecting to login, refreshes token on 401
- [ ] Scaffold web project:
  ```
  web/
  ├── src/
  │   ├── api/            # API client and hooks
  │   ├── auth/           # Auth context, login, guards
  │   ├── components/     # Shared UI components
  │   ├── features/       # Feature-specific components
  │   ├── hooks/          # Custom hooks
  │   ├── layouts/        # Page layouts (sidebar, topbar)
  │   ├── pages/          # Route pages
  │   ├── types/          # TypeScript type definitions
  │   └── utils/          # Utility functions
  ├── package.json
  ├── tsconfig.json
  ├── vite.config.ts
  ├── vitest.config.ts
  └── Dockerfile
  ```
- [ ] Install dependencies: React 18, TypeScript 5, Vite, TanStack Router, TanStack Query, Tailwind CSS, Vitest, Testing Library
- [ ] Implement: `web/src/api/client.ts` -- Axios/fetch wrapper with JWT interceptor, base URL from env
- [ ] Implement: `web/src/auth/AuthProvider.tsx` -- React context for auth state, login/logout methods, token storage in memory + refresh logic
- [ ] Implement: `web/src/auth/LoginPage.tsx` -- login form with email/password
- [ ] Implement: `web/src/auth/ProtectedRoute.tsx` -- route guard component
- [ ] Implement: `web/src/layouts/DashboardLayout.tsx` -- sidebar nav + top bar with user info
- [ ] Implement: `web/src/pages/DashboardPage.tsx` -- placeholder dashboard (authenticated shell)
- [ ] Configure routing: login route (public), dashboard routes (protected)
- [ ] Add web service to `docker-compose.dev.yml` with hot reload
- [ ] Verify: login flow works end-to-end, authenticated shell renders

**Exit Conditions**:

Build Verification:
- [ ] `cd web && npm run build` succeeds
- [ ] `cd web && npm run lint` passes (ESLint)
- [ ] `cd web && npx tsc --noEmit` passes (TypeScript)

Runtime Verification:
- [ ] `cd web && npm run dev` starts on port 3001 (or configured port)
- [ ] Login page renders at `/login`
- [ ] After login, dashboard shell renders with sidebar navigation

Functional Verification:
- [ ] `cd web && npm test` passes (Vitest)
- [ ] Login with valid credentials redirects to dashboard
- [ ] Login with invalid credentials shows error message
- [ ] Navigating to protected route without auth redirects to login

---

### Phase 13: Web Dashboard -- Team Overview and Athlete Views

**Objective**: Build the coach-facing dashboard pages: team overview (all athletes with key metrics at a glance), individual athlete detail view (ACWR chart, HRV trend, sleep summary, anomalies, wellness history), and training session list. After this phase, the coach can monitor their entire team from the web dashboard.

**Verification Approach**: Component tests verify data rendering and interaction. API hook tests verify correct data fetching.

**Tasks** (tests first, then implementation):

- [ ] Write test: `web/src/__tests__/features/TeamOverview.test.tsx` -- renders athlete cards with recovery score, ACWR zone badge, latest anomaly count, Garmin connection status
- [ ] Write test: `web/src/__tests__/features/AthleteDetail.test.tsx` -- renders ACWR chart, HRV trend chart, sleep summary, anomaly list, wellness history table
- [ ] Write test: `web/src/__tests__/features/SessionList.test.tsx` -- renders sessions with filters (date, type, source), session detail modal
- [ ] Write test: `web/src/__tests__/features/AnomalyFeed.test.tsx` -- renders anomaly cards with severity badge, explanation, metric context
- [ ] Write test: `web/src/__tests__/hooks/useAnalytics.test.ts` -- TanStack Query hooks: `useAthleteACWR`, `useAthleteHRV`, `useTeamOverview` fetch correct endpoints, handle loading/error states
- [ ] Implement API hooks: `web/src/api/hooks/useAthletes.ts`, `web/src/api/hooks/useAnalytics.ts`, `web/src/api/hooks/useSessions.ts`, `web/src/api/hooks/useWellness.ts`, `web/src/api/hooks/useAnomalies.ts`
- [ ] Implement: `web/src/types/api.ts` -- TypeScript types mirroring backend schemas (Athlete, Session, ACWR, HRV, Sleep, Anomaly, Recovery, Wellness)
- [ ] Implement: `web/src/features/team/TeamOverviewPage.tsx` -- grid of athlete cards showing:
  - Recovery score (color-coded 0-100)
  - ACWR zone (green/yellow/orange/red badge)
  - Last sync time
  - Active anomaly count
  - Garmin connection status indicator
- [ ] Implement: `web/src/features/athlete/AthleteDetailPage.tsx` -- athlete deep-dive:
  - ACWR chart (line chart, 28-day history, zone bands overlay)
  - HRV trend chart (RMSSD rolling mean + CV, 30-day)
  - Sleep summary (bar chart of nightly durations with stage breakdown)
  - Recovery score history (line chart, 14-day)
  - Active anomalies list
  - Recent wellness entries table
- [ ] Implement: `web/src/features/sessions/SessionListPage.tsx` -- filterable session list
- [ ] Implement: `web/src/features/anomalies/AnomalyFeed.tsx` -- team-wide anomaly feed (filterable by severity, athlete, metric)
- [ ] Implement chart components using a chart library (Recharts or Chart.js):
  - `web/src/components/charts/ACWRChart.tsx`
  - `web/src/components/charts/HRVTrendChart.tsx`
  - `web/src/components/charts/SleepChart.tsx`
  - `web/src/components/charts/RecoveryChart.tsx`
- [ ] Implement shared components: `AthleteCard.tsx`, `AnomalyCard.tsx`, `ZoneBadge.tsx`, `MetricValue.tsx`
- [ ] Add routes for all pages in router configuration
- [ ] Verify: all dashboard components render correctly with mock data

**Exit Conditions**:

Build Verification:
- [ ] `cd web && npm run build` succeeds
- [ ] `cd web && npm run lint` passes
- [ ] `cd web && npx tsc --noEmit` passes

Runtime Verification:
- [ ] Team overview page loads and displays athlete cards
- [ ] Clicking athlete card navigates to athlete detail page
- [ ] Charts render with data from backend API
- [ ] No console errors during navigation

Functional Verification:
- [ ] `cd web && npm test` passes
- [ ] Team overview shows correct number of athletes
- [ ] ACWR chart displays 28-day history with zone bands
- [ ] Anomaly feed shows anomalies sorted by severity then recency
- [ ] Session list filters work correctly (date range, type, source)

---

### Phase 14: Web Dashboard -- Manual Session Logging and Wellness

**Objective**: Build forms for coaches to log manual training sessions and view/manage wellness questionnaire submissions. After this phase, coaches can create sessions and review athlete wellness data from the dashboard.

**Verification Approach**: Form component tests verify validation, submission, and error handling. Integration tests verify data persistence through the full stack.

**Tasks** (tests first, then implementation):

- [ ] Write test: `web/src/__tests__/features/SessionForm.test.tsx` -- form renders all fields, validates required fields, submits to API, shows success/error feedback
- [ ] Write test: `web/src/__tests__/features/WellnessView.test.tsx` -- renders wellness history table, shows trend indicators, filters by date
- [ ] Implement: `web/src/features/sessions/SessionCreateForm.tsx` -- form for manual session logging:
  - Athlete selector (dropdown of team athletes)
  - Session type (match / training / gym / recovery)
  - Date and time pickers (start, end)
  - Duration (auto-calculated from start/end or manual entry)
  - Notes textarea
  - Optional metrics: distance, HR avg/max if known
  - Submit button with loading state
- [ ] Implement: `web/src/features/wellness/WellnessOverviewPage.tsx`:
  - Table of all athletes with today's wellness status (submitted / not submitted)
  - Per-athlete wellness trend sparklines (7-day mood, soreness, fatigue)
  - Click-through to athlete wellness detail
- [ ] Implement: `web/src/features/wellness/AthleteWellnessDetail.tsx`:
  - Wellness history table (date, sRPE, soreness, fatigue, mood, sleep quality, notes)
  - Trend charts for each wellness metric over time
- [ ] Add routes and navigation items for session creation and wellness views
- [ ] Verify: session creation and wellness viewing work end-to-end

**Exit Conditions**:

Build Verification:
- [ ] `cd web && npm run build` succeeds
- [ ] `cd web && npm run lint` passes
- [ ] `cd web && npx tsc --noEmit` passes

Runtime Verification:
- [ ] Session creation form renders and submits without errors
- [ ] Wellness overview page loads with correct athlete statuses
- [ ] No console errors

Functional Verification:
- [ ] `cd web && npm test` passes
- [ ] Manual session submission creates session in backend (verify via API)
- [ ] Wellness overview correctly shows which athletes have submitted today
- [ ] Wellness trend sparklines render for 7-day window

---

### Phase 15: Mobile App -- Project Setup and Authentication

**Objective**: Scaffold the React Native (Expo) mobile app for athletes. Implement login flow and basic navigation. After this phase, athletes can log in and see a basic home screen.

**Verification Approach**: Component tests verify login form and navigation. Auth flow tests verify token management.

**Tasks** (tests first, then implementation):

- [ ] Write test: `mobile/src/__tests__/auth/LoginScreen.test.tsx` -- form renders, validates, submits, handles errors
- [ ] Write test: `mobile/src/__tests__/auth/authStore.test.ts` -- secure token storage (expo-secure-store), auto-refresh, logout clears tokens
- [ ] Write test: `mobile/src/__tests__/navigation/AppNavigator.test.tsx` -- unauthenticated shows login, authenticated shows main tabs
- [ ] Scaffold Expo project:
  ```
  mobile/
  ├── src/
  │   ├── api/          # API client
  │   ├── auth/         # Auth store and screens
  │   ├── components/   # Shared components
  │   ├── features/     # Feature screens
  │   ├── navigation/   # Navigation config
  │   ├── hooks/        # Custom hooks
  │   ├── types/        # TypeScript types
  │   └── utils/        # Utilities
  ├── app.json
  ├── package.json
  ├── tsconfig.json
  └── babel.config.js
  ```
- [ ] Install dependencies: Expo SDK, React Navigation, TanStack Query, expo-secure-store, jest + Testing Library RN
- [ ] Implement: `mobile/src/api/client.ts` -- API client with secure token management
- [ ] Implement: `mobile/src/auth/authStore.ts` -- Zustand store for auth state with expo-secure-store persistence
- [ ] Implement: `mobile/src/auth/LoginScreen.tsx` -- login form
- [ ] Implement: `mobile/src/navigation/AppNavigator.tsx` -- tab navigator (Home, Profile, Settings) behind auth guard
- [ ] Implement: `mobile/src/features/home/HomeScreen.tsx` -- placeholder home screen showing athlete name and team
- [ ] Verify: login flow works on Expo Go (Android)

**Exit Conditions**:

Build Verification:
- [ ] `cd mobile && npx expo export --platform android` succeeds (or `npx tsc --noEmit`)
- [ ] `cd mobile && npm run lint` passes

Runtime Verification:
- [ ] Expo Go app launches without crashes
- [ ] Login screen renders on app open
- [ ] After login, home screen displays with tab navigation

Functional Verification:
- [ ] `cd mobile && npm test` passes
- [ ] Login with valid credentials navigates to home
- [ ] Login with invalid credentials shows error
- [ ] App token persists across app restart (secure store)

---

### Phase 16: Mobile App -- Garmin Connection and Athlete Features

**Objective**: Build the athlete-facing features: Garmin device linking (via Open Wearables OAuth), daily wellness questionnaire submission, personal metrics dashboard (recovery score, ACWR, HRV), and session history. After this phase, athletes have a fully functional mobile experience.

**Verification Approach**: Component tests verify all screens. Integration tests verify Garmin connection flow and wellness submission.

**Tasks** (tests first, then implementation):

- [ ] Write test: `mobile/src/__tests__/features/GarminConnect.test.tsx` -- shows connect button when disconnected, shows connected status when linked, opens OAuth URL in in-app browser
- [ ] Write test: `mobile/src/__tests__/features/WellnessForm.test.tsx` -- renders all fields with sliders/pickers, validates ranges, submits to API, shows today's existing entry for edit
- [ ] Write test: `mobile/src/__tests__/features/MetricsDashboard.test.tsx` -- renders recovery score (prominent), ACWR zone, HRV trend mini-chart, last night sleep summary
- [ ] Write test: `mobile/src/__tests__/features/SessionHistory.test.tsx` -- renders recent sessions with type icons, source badges (garmin/manual), basic metrics
- [ ] Implement: `mobile/src/features/garmin/GarminConnectScreen.tsx`:
  - Connection status indicator (connected / not connected / syncing)
  - Connect button -> opens OW OAuth URL in WebBrowser
  - Callback handling to confirm connection
  - Last sync time display
- [ ] Implement: `mobile/src/features/wellness/WellnessFormScreen.tsx`:
  - sRPE slider (1-10) with session duration picker
  - Soreness body map or slider (1-10)
  - Fatigue slider (1-10)
  - Mood picker (1-5 with emoji faces)
  - Sleep quality (1-5)
  - Notes text input
  - Submit with confirmation feedback
  - Pre-fill if today's entry already exists (edit mode)
- [ ] Implement: `mobile/src/features/dashboard/MetricsDashboardScreen.tsx`:
  - Recovery score (large circular gauge, 0-100, color-coded)
  - ACWR zone indicator with value
  - HRV 7-day sparkline
  - Last night sleep (duration + efficiency)
  - Active anomalies (if any, with explanations)
- [ ] Implement: `mobile/src/features/sessions/SessionHistoryScreen.tsx`:
  - Scrollable list of recent sessions (last 30 days)
  - Session type icon + source badge
  - Basic metrics (duration, HR avg, distance)
  - Tap to expand for detail
- [ ] Implement: `mobile/src/features/profile/ProfileScreen.tsx`:
  - Athlete profile info (editable: position, height, weight)
  - Garmin connection management
  - Notification preferences (future)
- [ ] Implement API hooks for mobile: `mobile/src/api/hooks/` (mirror web hooks adapted for RN)
- [ ] Verify: all mobile features work on Expo Go

**Exit Conditions**:

Build Verification:
- [ ] `cd mobile && npx tsc --noEmit` passes
- [ ] `cd mobile && npm run lint` passes

Runtime Verification:
- [ ] All screens render without crashes on Expo Go
- [ ] Garmin connect button opens OAuth URL
- [ ] Wellness form submits successfully
- [ ] Dashboard shows metrics from backend

Functional Verification:
- [ ] `cd mobile && npm test` passes
- [ ] Wellness form validates field ranges (rejects sRPE > 10)
- [ ] Wellness form shows today's existing entry in edit mode
- [ ] Recovery score displays with correct color coding
- [ ] Session history shows both garmin and manual sessions

---

### Phase 17: Data Seeding, End-to-End Testing, and Polish

**Objective**: Create a comprehensive seed script generating realistic test data for a full football team (25 athletes, 90 days of data). Build end-to-end tests covering critical user journeys. Fix edge cases and polish UX. After this phase, the platform is demo-ready and functionally complete for V1.

**Verification Approach**: E2E tests cover the critical paths: coach login -> team overview -> athlete detail -> anomaly review. Seed data produces realistic analytics values.

**Tasks** (tests first, then implementation):

- [ ] Write test: `backend/tests/e2e/test_coach_journey.py` -- full flow: register coach -> create team -> add athletes -> log sessions -> view analytics -> check anomalies
- [ ] Write test: `backend/tests/e2e/test_athlete_journey.py` -- full flow: athlete login -> submit wellness -> view dashboard -> check recovery score
- [ ] Write test: `backend/tests/e2e/test_sync_journey.py` -- full flow: athlete connects Garmin (mocked) -> data syncs -> analytics computed -> visible in dashboard
- [ ] Implement: `backend/app/db/seed.py` -- comprehensive seed script:
  - 1 team ("FC Demo")
  - 2 coaches
  - 25 athletes with varied profiles (positions, ages)
  - 90 days of synthetic metric data per athlete (realistic distributions):
    - Resting HR: 45-65 bpm base, daily variation +/- 5
    - HRV RMSSD: 40-80ms base, daily variation +/- 15
    - Sleep: 6-9 hours, realistic stage distribution
    - Training load: periodized (3 weeks build, 1 week recovery)
    - 2-3 planted anomalies per athlete (sudden drops/spikes)
  - 90 days of training sessions (mix of garmin-sourced and manual)
  - 60 days of wellness entries per athlete (some missing days)
- [ ] Implement: `Makefile` seed target: `make seed` runs seed script
- [ ] Fix edge cases discovered during E2E testing
- [ ] Polish: error messages, loading states, empty states on all frontend pages
- [ ] Implement: error boundary component for web dashboard
- [ ] Implement: network error handling and retry UI for mobile
- [ ] Update `docker-compose.yml` with production-ready defaults
- [ ] Create `.env.example` with all required environment variables documented
- [ ] Verify: full platform works end-to-end with seeded data

**Exit Conditions**:

Build Verification:
- [ ] `docker compose build` succeeds for all services
- [ ] `docker compose run backend ruff check app/` passes
- [ ] `docker compose run backend mypy app/` passes
- [ ] `cd web && npm run build` succeeds
- [ ] `cd mobile && npx tsc --noEmit` passes

Runtime Verification:
- [ ] `docker compose up` starts all services (backend, web, DB, Redis, Celery, OW)
- [ ] `make seed` populates database with demo data in < 60 seconds
- [ ] Web dashboard loads team overview with 25 athletes
- [ ] Mobile app loads athlete dashboard with metrics
- [ ] No console errors across all frontends

Functional Verification:
- [ ] `docker compose run backend pytest tests/e2e/` passes
- [ ] `cd web && npm test` passes
- [ ] `cd mobile && npm test` passes
- [ ] `docker compose run backend pytest` passes (full test suite)
- [ ] Team overview shows ACWR zones distributed across athletes (not all same)
- [ ] At least 2 anomalies visible in anomaly feed from seeded data
- [ ] Recovery scores range from 30-95 across athletes (realistic spread)
- [ ] Coach can navigate: login -> team overview -> athlete detail -> ACWR chart -> anomaly -> back
- [ ] `.env.example` documents all required environment variables

## Dependencies

### External Dependencies
- **Open Wearables v0.3.0-beta**: Core middleware. Pin version in docker-compose to avoid breaking changes. Monitor [releases](https://github.com/the-momentum/open-wearables/releases) for API changes.
- **Garmin Developer Program**: Requires approved developer account for Health API access. OAuth 1.0a consumer key/secret needed. Apply early as approval may take 1-2 weeks.
- **Docker + Docker Compose**: Required for local development and deployment.
- **Node.js 20+**: For web and mobile development.
- **Python 3.12+**: For backend development.
- **uv**: Python package manager (fast alternative to pip).

### Internal Dependencies (Phase Ordering)
- Phase 1 (scaffolding) blocks all other phases
- Phases 2-3 (models, auth) block all API phases
- Phase 4 (OW integration) blocks Phase 5 (sync tasks)
- Phases 6-7 (management API) can proceed in parallel with Phase 4
- Phases 8-10 (analytics) depend on Phase 7 (session/wellness data) and Phase 5 (synced data)
- Phase 11 (TimescaleDB optimization) depends on Phases 8-10 having established query patterns
- Phase 12 (web setup) can proceed in parallel with backend Phases 4-10
- Phase 13 (web dashboard) depends on Phase 12 (web setup) + Phases 8-10 (analytics API)
- Phase 14 (web forms) depends on Phase 13
- Phase 15 (mobile setup) can proceed in parallel with Phase 12
- Phase 16 (mobile features) depends on Phase 15 + Phases 8-10
- Phase 17 (E2E) depends on all prior phases

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Open Wearables API changes (pre-1.0) | Medium | High | Pin OW version, wrap all OW calls in client abstraction layer (Phase 4), monitor changelog |
| Garmin developer approval delay | Medium | Medium | Apply immediately, use OW seed data for development until approved |
| TimescaleDB continuous aggregate limitations | Low | Medium | Fallback to regular materialized views with scheduled refresh if needed |
| OW webhook reliability (beta software) | Medium | Medium | Implement polling fallback in sync tasks, store last successful sync timestamp per athlete |
| React Native Expo limitations for future Apple Health | Low | Low | V1 only uses Garmin (cloud API). Evaluate Flutter migration for V2 if Apple Health SDK integration proves difficult |
| Performance at scale (>100 athletes) | Low | Medium | TimescaleDB handles time-series well, continuous aggregates prevent repeated computation. Add read replicas if needed |
| ACWR scientific validity debates | Low | Low | EWMA is currently accepted best practice. Make decay constants configurable for future adjustment |
