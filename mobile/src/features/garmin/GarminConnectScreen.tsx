import React from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { useProfile } from '@/api/hooks/useProfile';
import { API_URL } from '@/utils/constants';

export function GarminConnectScreen() {
  const profile = useProfile();

  const garminConnected = profile.data?.garmin_connected ?? false;
  const lastSyncAt = profile.data?.last_sync_at;

  const handleConnect = async () => {
    const oauthUrl = `${API_URL}/api/v1/garmin/oauth/start`;
    await Linking.openURL(oauthUrl);
  };

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>Garmin Connection</Text>

        <View style={styles.statusRow}>
          <View
            style={[
              styles.statusDot,
              {
                backgroundColor: garminConnected ? '#22c55e' : '#ef4444',
              },
            ]}
          />
          <Text style={styles.statusText} testID="garmin-connection-status">
            {garminConnected ? 'Connected' : 'Not Connected'}
          </Text>
        </View>

        {lastSyncAt && (
          <Text style={styles.syncText}>
            Last sync: {new Date(lastSyncAt).toLocaleString()}
          </Text>
        )}

        {!garminConnected && (
          <Pressable
            style={styles.connectButton}
            onPress={handleConnect}
            testID="garmin-connect-button"
          >
            <Text style={styles.connectButtonText}>Connect Garmin</Text>
          </Pressable>
        )}

        {garminConnected && (
          <View style={styles.connectedInfo}>
            <Text style={styles.connectedText}>
              Your Garmin device is connected. Data syncs automatically.
            </Text>
          </View>
        )}
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
    marginBottom: 20,
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
  connectedInfo: {
    marginTop: 8,
  },
  connectedText: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
  },
});
