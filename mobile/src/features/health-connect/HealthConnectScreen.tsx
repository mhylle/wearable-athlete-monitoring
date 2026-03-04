import React from 'react';
import { ActivityIndicator, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import {
  isHealthConnectAvailable,
  useHealthDataSync,
  useHealthSyncStatus,
  useRequestHealthPermissions,
} from './useHealthDataSync';

export function HealthConnectScreen() {
  const status = useHealthSyncStatus();
  const syncMutation = useHealthDataSync();
  const permissionMutation = useRequestHealthPermissions();

  const isAvailable = isHealthConnectAvailable();
  const connected = status.data?.connected ?? false;
  const lastSyncAt = status.data?.last_sync_at;
  const isSyncing = syncMutation.isPending;

  const handleConnect = async () => {
    try {
      await permissionMutation.mutateAsync();
      // After permissions granted, do an initial sync (last 30 days)
      syncMutation.mutate({ days: 30 });
    } catch {
      // Error is captured in permissionMutation.error — displayed below
    }
  };

  const handleSync = () => {
    syncMutation.mutate({ days: 7 });
  };

  if (Platform.OS !== 'android') {
    return (
      <View style={styles.container}>
        <View style={styles.card}>
          <Text style={styles.title}>Health Connect</Text>
          <Text style={styles.unavailableText}>
            Health Connect is only available on Android devices with a Pixel
            Watch or other Wear OS watch.
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>Health Connect</Text>

        <View style={styles.statusRow}>
          <View
            style={[
              styles.statusDot,
              { backgroundColor: connected ? '#22c55e' : '#ef4444' },
            ]}
          />
          <Text style={styles.statusText} testID="hc-connection-status">
            {connected ? 'Connected' : 'Not Connected'}
          </Text>
        </View>

        {lastSyncAt && (
          <Text style={styles.syncText}>
            Last sync: {new Date(lastSyncAt).toLocaleString()}
          </Text>
        )}

        {syncMutation.isSuccess && (
          <View style={styles.resultBox}>
            <Text style={styles.resultText}>
              Synced {syncMutation.data.metrics_synced} metrics,{' '}
              {syncMutation.data.sessions_synced} sessions
            </Text>
          </View>
        )}

        {/* Permission error feedback */}
        {permissionMutation.isError && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>
              {permissionMutation.error?.message ?? 'Failed to connect to Health Connect.'}
            </Text>
          </View>
        )}

        {/* Sync error feedback */}
        {syncMutation.isError && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>
              Sync failed: {syncMutation.error?.message ?? 'Unknown error'}
            </Text>
          </View>
        )}

        {!isAvailable && (
          <View style={styles.warningBox}>
            <Text style={styles.warningText}>
              Health Connect SDK not available. Please install this app as a
              development build to enable Health Connect integration.
            </Text>
          </View>
        )}

        {isAvailable && !connected && (
          <Pressable
            style={styles.connectButton}
            onPress={handleConnect}
            disabled={permissionMutation.isPending}
            testID="hc-connect-button"
          >
            <Text style={styles.connectButtonText}>
              {permissionMutation.isPending
                ? 'Requesting Permissions...'
                : 'Connect Health Connect'}
            </Text>
          </Pressable>
        )}

        {connected && (
          <>
            <Text style={styles.connectedText}>
              Your health data syncs from Health Connect. Tap below to sync now.
            </Text>
            <Pressable
              style={[styles.syncButton, isSyncing && styles.syncButtonDisabled]}
              onPress={handleSync}
              disabled={isSyncing}
              testID="hc-sync-button"
            >
              {isSyncing ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Text style={styles.syncButtonText}>Sync Now</Text>
              )}
            </Pressable>
          </>
        )}
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>Supported Data</Text>
        <Text style={styles.infoText}>
          Heart Rate, HRV, Resting Heart Rate, Steps, Sleep, Exercise Sessions,
          VO2 Max, SpO2
        </Text>
        <Text style={[styles.infoText, { marginTop: 8 }]}>
          Data is read from Health Connect on your phone, which receives it from
          your Google/Pixel Watch.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
    padding: 20,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 20,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 12,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  statusText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  syncText: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 16,
  },
  resultBox: {
    backgroundColor: '#f0fdf4',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  resultText: {
    fontSize: 14,
    color: '#166534',
  },
  errorBox: {
    backgroundColor: '#fef2f2',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
    color: '#991b1b',
    lineHeight: 20,
  },
  warningBox: {
    backgroundColor: '#fef3c7',
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  warningText: {
    fontSize: 14,
    color: '#92400e',
    lineHeight: 20,
  },
  unavailableText: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
  },
  connectButton: {
    height: 48,
    backgroundColor: '#2563eb',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  connectButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  connectedText: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
    marginBottom: 12,
  },
  syncButton: {
    height: 48,
    backgroundColor: '#16a34a',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  syncButtonDisabled: {
    opacity: 0.6,
  },
  syncButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
  },
});
