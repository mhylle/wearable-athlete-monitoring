# Session: Vitals Dashboard + Live Health Connect Sync

**Date**: March 4, 2026

## What Was Done

### Phase 1: Backend — Metrics Query Endpoints
- Created `backend/app/api/metrics_router.py` with two endpoints:
  - `GET /api/v1/metrics/athlete/{id}/daily` — daily-aggregated metrics (avg, min, max, count)
  - `GET /api/v1/metrics/athlete/{id}/available` — lists metric types with data
- Created `backend/app/api/schemas/metrics.py` — Pydantic response models
- Registered router in `backend/app/main.py`

### Phase 2: Mobile — Vitals Screen with Charts
- Installed `react-native-chart-kit` in mobile app
- Created `mobile/src/api/hooks/useMetrics.ts` — React Query hooks for metrics API
- Created `mobile/src/features/vitals/VitalsScreen.tsx` — scrollable vitals dashboard with line charts for 8 metric types (HR, HRV, Resting HR, Steps, Sleep, SpO2, VO2 Max)
- Updated `mobile/src/navigation/AppNavigator.tsx` — replaced Home tab with Vitals tab
- Tab order: Vitals | Wellness | Sessions | Health | Profile

### Phase 3: Web — Vitals View
- Added metric hooks to `web/src/api/hooks/useAnalytics.ts`
- Created `web/src/components/charts/MetricLineChart.tsx` — Recharts line chart with min/max shaded area
- Added vitals section to `web/src/features/athlete/AthleteDetailPage.tsx`
- Created `web/src/features/vitals/MyVitalsPage.tsx` — personal vitals page
- Added `/my-vitals` route and nav item

### Phase 4: Live Data & Bug Fixes

#### Health Connect Permissions Bug (Critical Fix)
**Problem**: After APK reinstall, Health Connect permissions were reset. The app silently returned 0 metrics because:
1. `readHealthData()` has silent `catch {}` blocks that swallow permission errors
2. `isHealthConnectAvailable()` only checks SDK availability, not permissions
3. HealthConnectScreen showed "Connected" based on backend status, hiding the permissions button

**Fix**: Added `await requestPermissions()` at the start of `useHealthDataSync`'s `mutationFn` to ensure permissions are granted before every sync attempt.

**Result**: Successfully synced 2,049 metrics from Pixel Watch 4 via Health Connect.

#### Login Screen Keyboard Navigation
**Problem**: `adb shell input tap` couldn't reliably tap the password field in React Native.

**Fix**: Added keyboard navigation with `returnKeyType="next"`, `onSubmitEditing`, and `useRef` for field-to-field focus.

#### TimescaleDB Continuous Aggregate Refresh
**Problem**: After bulk data sync, charts showed stale data because the continuous aggregate hadn't refreshed.

**Fix**: Manual refresh: `CALL refresh_continuous_aggregate('daily_metric_agg', '2026-03-01', '2026-03-05');`

**Note**: Should be automated via Celery task or TimescaleDB refresh policy.

## Key Decisions
- Used release APK builds instead of Expo dev client (Metro connection over adb reverse was unreliable for 8MB bundles)
- Kept all 8 metric types in VitalsScreen even if data isn't always available (shows "No data available" per card)
- Auto-sync on VitalsScreen mount with 3-day lookback
- Pull-to-refresh triggers Health Connect sync then chart reload

## Files Changed (280 files total in commit)
Key files:
| File | Action |
|------|--------|
| `backend/app/api/metrics_router.py` | Created |
| `backend/app/api/schemas/metrics.py` | Created |
| `backend/app/main.py` | Modified |
| `mobile/src/api/hooks/useMetrics.ts` | Created |
| `mobile/src/features/vitals/VitalsScreen.tsx` | Created |
| `mobile/src/navigation/AppNavigator.tsx` | Modified |
| `mobile/src/auth/LoginScreen.tsx` | Modified |
| `mobile/src/features/health-connect/useHealthDataSync.ts` | Modified |
| `web/src/api/hooks/useAnalytics.ts` | Modified |
| `web/src/components/charts/MetricLineChart.tsx` | Created |
| `web/src/features/athlete/AthleteDetailPage.tsx` | Modified |
| `web/src/features/vitals/MyVitalsPage.tsx` | Created |
| `web/src/App.tsx` | Modified |
| `web/src/layouts/DashboardLayout.tsx` | Modified |
| `.gitignore` | Modified |

## Known Issues / Future Work
- Heart rate data from Pixel Watch 4 lags 1-2 days (watch batches HR differently from sleep data)
- Silent `catch {}` blocks in `healthConnectService.ts` should log errors instead of swallowing them
- TimescaleDB continuous aggregate refresh should be automated after sync
- HealthConnectScreen "Connected" status should check actual device permissions, not just backend state
