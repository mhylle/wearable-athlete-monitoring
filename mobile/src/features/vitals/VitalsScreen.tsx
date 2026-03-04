import React from 'react';
import {
  ScrollView,
  View,
  Text,
  StyleSheet,
  Dimensions,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import {
  useAvailableMetrics,
  useMetricSeries,
  type DailyMetricDataPoint,
} from '@/api/hooks/useMetrics';
import {
  useHealthDataSync,
  isHealthConnectAvailable,
} from '@/features/health-connect/useHealthDataSync';

const SCREEN_WIDTH = Dimensions.get('window').width;
const CHART_WIDTH = SCREEN_WIDTH - 48;

interface MetricConfig {
  key: string;
  label: string;
  unit: string;
  color: string;
}

const TIME_METRICS = new Set(['sleep_total', 'sleep_light']);

function formatMinutes(minutes: number): string {
  const totalSeconds = Math.round(minutes * 60);
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

const METRIC_CONFIGS: MetricConfig[] = [
  { key: 'heart_rate', label: 'Heart Rate', unit: 'bpm', color: '#ef4444' },
  { key: 'hrv_rmssd', label: 'HRV (RMSSD)', unit: 'ms', color: '#8b5cf6' },
  { key: 'resting_hr', label: 'Resting HR', unit: 'bpm', color: '#f97316' },
  { key: 'steps', label: 'Steps', unit: 'steps', color: '#22c55e' },
  { key: 'sleep_total', label: 'Sleep Total', unit: '', color: '#3b82f6' },
  { key: 'sleep_light', label: 'Sleep Light', unit: '', color: '#a78bfa' },
  { key: 'spo2', label: 'SpO2', unit: '%', color: '#06b6d4' },
  { key: 'vo2_max', label: 'VO2 Max', unit: 'ml/kg/min', color: '#ec4899' },
];

function MetricCard({ config, available }: { config: MetricConfig; available: boolean }) {
  const { data, isLoading } = useMetricSeries(available ? config.key : '', 30);

  if (!available) return null;

  const points = data?.data ?? [];

  if (isLoading) {
    return (
      <View style={styles.card}>
        <Text style={styles.cardTitle}>{config.label}</Text>
        <ActivityIndicator size="small" color={config.color} style={styles.loader} />
      </View>
    );
  }

  if (points.length === 0) {
    return (
      <View style={styles.card}>
        <Text style={styles.cardTitle}>{config.label}</Text>
        <Text style={styles.emptyText}>No data available</Text>
      </View>
    );
  }

  const latest = points[points.length - 1];
  const minVal = Math.min(...points.map((p: DailyMetricDataPoint) => p.min));
  const maxVal = Math.max(...points.map((p: DailyMetricDataPoint) => p.max));

  const isTime = TIME_METRICS.has(config.key);
  const fmtVal = (v: number) =>
    isTime ? formatMinutes(v) : `${v.toFixed(config.key === 'steps' ? 0 : 1)} ${config.unit}`;

  // Show at most 14 labels on x-axis
  const labels = points.map((p: DailyMetricDataPoint) => {
    const d = new Date(p.date);
    return `${d.getMonth() + 1}/${d.getDate()}`;
  });
  const chartData = points.map((p: DailyMetricDataPoint) => p.avg);

  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{config.label}</Text>
        <Text style={[styles.latestValue, { color: config.color }]}>
          {fmtVal(latest.avg)}
        </Text>
      </View>

      <LineChart
        data={{
          labels: labels.filter((_, i) => i % Math.ceil(labels.length / 7) === 0),
          datasets: [{ data: chartData, color: () => config.color, strokeWidth: 2 }],
        }}
        width={CHART_WIDTH}
        height={180}
        chartConfig={{
          backgroundColor: '#ffffff',
          backgroundGradientFrom: '#ffffff',
          backgroundGradientTo: '#ffffff',
          decimalPlaces: config.key === 'steps' ? 0 : 1,
          color: () => config.color,
          labelColor: () => '#9ca3af',
          propsForDots: { r: '0' },
          propsForBackgroundLines: { stroke: '#f3f4f6' },
        }}
        bezier
        withInnerLines={false}
        style={styles.chart}
      />

      <View style={styles.minMaxRow}>
        <Text style={styles.minMaxText}>Min: {fmtVal(minVal)}</Text>
        <Text style={styles.minMaxText}>Max: {fmtVal(maxVal)}</Text>
      </View>
    </View>
  );
}

export function VitalsScreen() {
  const { data: available, isLoading, refetch } = useAvailableMetrics();
  const syncMutation = useHealthDataSync();
  const [refreshing, setRefreshing] = React.useState(false);
  const hasSynced = React.useRef(false);

  // Auto-sync from Health Connect on first mount
  React.useEffect(() => {
    if (!hasSynced.current && isHealthConnectAvailable()) {
      hasSynced.current = true;
      syncMutation.mutate({ days: 3 });
    }
  }, []);

  // Pull-to-refresh: sync from Health Connect then reload charts
  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    if (isHealthConnectAvailable()) {
      syncMutation.mutate(
        { days: 3 },
        {
          onSettled: () => {
            refetch().finally(() => setRefreshing(false));
          },
        },
      );
    } else {
      refetch().finally(() => setRefreshing(false));
    }
  }, [refetch, syncMutation]);

  const availableTypes = available?.metric_types ?? [];
  const isSyncing = syncMutation.isPending;

  if (isLoading && !refreshing) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2563eb" />
        <Text style={styles.loadingText}>Loading vitals...</Text>
      </View>
    );
  }

  if (availableTypes.length === 0 && !isSyncing) {
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.centered}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        <Text style={styles.emptyTitle}>No Vitals Data Yet</Text>
        <Text style={styles.emptySubtitle}>
          Connect Health Connect and sync to see your vitals.
        </Text>
      </ScrollView>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {isSyncing && (
        <View style={styles.syncBanner}>
          <ActivityIndicator size="small" color="#2563eb" />
          <Text style={styles.syncText}>Syncing from Health Connect...</Text>
        </View>
      )}
      {syncMutation.isSuccess && !isSyncing && (
        <View style={styles.syncBannerSuccess}>
          <Text style={styles.syncTextSuccess}>
            Synced {syncMutation.data.metrics_synced} metrics
          </Text>
        </View>
      )}
      {METRIC_CONFIGS.map((config) => (
        <MetricCard
          key={config.key}
          config={config}
          available={availableTypes.includes(config.key)}
        />
      ))}
      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    lineHeight: 20,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    marginHorizontal: 16,
    marginTop: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
  },
  latestValue: {
    fontSize: 16,
    fontWeight: '700',
  },
  chart: {
    borderRadius: 8,
    marginLeft: -16,
  },
  minMaxRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  minMaxText: {
    fontSize: 12,
    color: '#9ca3af',
  },
  loader: {
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 13,
    color: '#9ca3af',
    textAlign: 'center',
    paddingVertical: 24,
  },
  syncBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginHorizontal: 16,
    marginTop: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: '#eff6ff',
    borderRadius: 8,
  },
  syncText: {
    fontSize: 13,
    color: '#2563eb',
    fontWeight: '500',
  },
  syncBannerSuccess: {
    alignItems: 'center',
    marginHorizontal: 16,
    marginTop: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: '#f0fdf4',
    borderRadius: 8,
  },
  syncTextSuccess: {
    fontSize: 13,
    color: '#16a34a',
    fontWeight: '500',
  },
  bottomSpacer: {
    height: 24,
  },
});
