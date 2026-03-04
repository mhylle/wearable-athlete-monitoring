import React from 'react';
import {
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useAuthStore } from '@/auth/authStore';
import {
  useRecoveryScore,
  useACWR,
  useHRV,
  useSleep,
  useAnomalies,
} from '@/api/hooks/useAnalytics';
import { Sparkline } from '@/components/Sparkline';

function getRecoveryColor(score: number): string {
  if (score < 40) return '#ef4444';
  if (score <= 70) return '#f59e0b';
  return '#22c55e';
}

function getACWRZoneLabel(zone: string): string {
  const labels: Record<string, string> = {
    undertraining: 'Undertraining',
    optimal: 'Optimal',
    caution: 'Caution',
    high_risk: 'High Risk',
  };
  return labels[zone] ?? zone;
}

function getACWRZoneColor(zone: string): string {
  const colors: Record<string, string> = {
    undertraining: '#3b82f6',
    optimal: '#22c55e',
    caution: '#f59e0b',
    high_risk: '#ef4444',
  };
  return colors[zone] ?? '#9ca3af';
}

function formatSleepDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  return `${hours}h ${mins}m`;
}

export function HomeScreen() {
  const user = useAuthStore((s) => s.user);
  const recovery = useRecoveryScore();
  const acwr = useACWR();
  const hrv = useHRV();
  const sleep = useSleep();
  const anomalies = useAnomalies();

  const [refreshing, setRefreshing] = React.useState(false);

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    Promise.all([
      recovery.refetch(),
      acwr.refetch(),
      hrv.refetch(),
      sleep.refetch(),
      anomalies.refetch(),
    ]).finally(() => setRefreshing(false));
  }, [recovery, acwr, hrv, sleep, anomalies]);

  // ACWR: backend returns single object, not array
  const acwrData = acwr.data;

  // Sleep: backend returns { daily_summaries: [...] }
  const dailySummaries = sleep.data?.daily_summaries ?? [];
  const latestSleep = dailySummaries.length > 0
    ? dailySummaries[dailySummaries.length - 1]
    : undefined;

  // HRV: backend returns { stats: { rolling_mean, ... }, daily_values: [{ date, rmssd }] }
  const hrvValues = hrv.data?.daily_values?.map((h) => h.rmssd) ?? [];

  // Recovery: check if any components have data
  const hasRecoveryData =
    recovery.data != null &&
    recovery.data.available_components.length > 0 &&
    recovery.data.total_score != null;

  // Anomalies: backend returns { anomalies: [...] }
  const anomalyList = anomalies.data?.anomalies ?? [];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <Text style={styles.greeting}>
        Welcome, {user?.full_name ?? 'Athlete'}
      </Text>
      {user?.team_id && <Text style={styles.teamInfo}>Team member</Text>}

      <View style={styles.cards}>
        {/* Recovery Score */}
        <View style={styles.card} testID="recovery-card">
          <Text style={styles.cardTitle}>Recovery Score</Text>
          {hasRecoveryData ? (
            <View style={styles.recoveryContainer}>
              <View
                style={[
                  styles.recoveryGauge,
                  {
                    borderColor: getRecoveryColor(recovery.data!.total_score!),
                  },
                ]}
              >
                <Text
                  style={[
                    styles.recoveryScore,
                    { color: getRecoveryColor(recovery.data!.total_score!) },
                  ]}
                  testID="recovery-score"
                >
                  {Math.round(recovery.data!.total_score!)}
                </Text>
                <Text style={styles.recoveryLabel}>/ 100</Text>
              </View>
              <View style={styles.recoveryBreakdown}>
                {recovery.data!.hrv_component != null && (
                  <Text style={styles.breakdownItem}>
                    HRV: {Math.round(recovery.data!.hrv_component)}
                  </Text>
                )}
                {recovery.data!.sleep_component != null && (
                  <Text style={styles.breakdownItem}>
                    Sleep: {Math.round(recovery.data!.sleep_component)}
                  </Text>
                )}
                {recovery.data!.load_component != null && (
                  <Text style={styles.breakdownItem}>
                    Load: {Math.round(recovery.data!.load_component)}
                  </Text>
                )}
                {recovery.data!.subjective_component != null && (
                  <Text style={styles.breakdownItem}>
                    Wellness: {Math.round(recovery.data!.subjective_component)}
                  </Text>
                )}
              </View>
            </View>
          ) : (
            <Text style={styles.noData}>
              {recovery.isLoading ? 'Loading...' : 'No data available'}
            </Text>
          )}
        </View>

        {/* ACWR Zone */}
        <View style={styles.card} testID="acwr-card">
          <Text style={styles.cardTitle}>Training Load (ACWR)</Text>
          {acwrData ? (
            <View style={styles.acwrContainer}>
              <Text style={styles.acwrValue}>
                {(acwrData.acwr_value ?? 0).toFixed(2)}
              </Text>
              <View
                style={[
                  styles.acwrBadge,
                  { backgroundColor: getACWRZoneColor(acwrData.zone) },
                ]}
              >
                <Text style={styles.acwrBadgeText} testID="acwr-zone">
                  {getACWRZoneLabel(acwrData.zone)}
                </Text>
              </View>
            </View>
          ) : (
            <Text style={styles.noData}>
              {acwr.isLoading ? 'Loading...' : 'No data available'}
            </Text>
          )}
        </View>

        {/* HRV Trend */}
        <View style={styles.card} testID="hrv-card">
          <Text style={styles.cardTitle}>HRV Trend (7-day)</Text>
          {hrv.data ? (
            <View style={styles.hrvContainer}>
              <View style={styles.hrvStats}>
                <Text style={styles.hrvMean}>
                  {(hrv.data.stats?.rolling_mean ?? 0).toFixed(1)} ms
                </Text>
                <Text style={styles.hrvTrend}>
                  Trend: {hrv.data.stats?.trend ?? 'unknown'}
                </Text>
              </View>
              {hrvValues.length >= 2 && (
                <Sparkline data={hrvValues} width={140} height={40} />
              )}
            </View>
          ) : (
            <Text style={styles.noData}>
              {hrv.isLoading ? 'Loading...' : 'No data available'}
            </Text>
          )}
        </View>

        {/* Sleep */}
        <View style={styles.card} testID="sleep-card">
          <Text style={styles.cardTitle}>Last Night Sleep</Text>
          {latestSleep ? (
            <View style={styles.sleepContainer}>
              <Text style={styles.sleepDuration}>
                {formatSleepDuration(latestSleep.total_minutes)}
              </Text>
              <Text style={styles.sleepEfficiency}>
                {Math.round(latestSleep.efficiency * 100)}% efficiency
              </Text>
            </View>
          ) : (
            <Text style={styles.noData}>
              {sleep.isLoading ? 'Loading...' : 'No data available'}
            </Text>
          )}
        </View>

        {/* Anomalies */}
        {anomalyList.length > 0 && (
          <View style={[styles.card, styles.anomalyCard]} testID="anomalies-card">
            <Text style={styles.cardTitle}>Active Anomalies</Text>
            {anomalyList.map((anomaly, index) => (
              <View key={index} style={styles.anomalyItem}>
                <View
                  style={[
                    styles.severityDot,
                    {
                      backgroundColor:
                        anomaly.severity === 'high'
                          ? '#ef4444'
                          : anomaly.severity === 'medium'
                            ? '#f59e0b'
                            : '#3b82f6',
                    },
                  ]}
                />
                <Text style={styles.anomalyText}>{anomaly.explanation}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  content: {
    padding: 20,
  },
  greeting: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  teamInfo: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 24,
  },
  cards: {
    gap: 16,
    marginTop: 16,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6b7280',
    marginBottom: 12,
  },
  noData: {
    fontSize: 14,
    color: '#9ca3af',
  },
  recoveryContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 20,
  },
  recoveryGauge: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 6,
    justifyContent: 'center',
    alignItems: 'center',
  },
  recoveryScore: {
    fontSize: 32,
    fontWeight: '700',
  },
  recoveryLabel: {
    fontSize: 12,
    color: '#9ca3af',
  },
  recoveryBreakdown: {
    flex: 1,
    gap: 4,
  },
  breakdownItem: {
    fontSize: 14,
    color: '#374151',
  },
  acwrContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  acwrValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
  },
  acwrBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
  },
  acwrBadgeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  hrvContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  hrvStats: {
    gap: 4,
  },
  hrvMean: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
  hrvTrend: {
    fontSize: 14,
    color: '#6b7280',
    textTransform: 'capitalize',
  },
  sleepContainer: {
    gap: 4,
  },
  sleepDuration: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
  sleepEfficiency: {
    fontSize: 14,
    color: '#6b7280',
  },
  anomalyCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#f59e0b',
  },
  anomalyItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 8,
  },
  severityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginTop: 5,
  },
  anomalyText: {
    fontSize: 14,
    color: '#374151',
    flex: 1,
  },
});
