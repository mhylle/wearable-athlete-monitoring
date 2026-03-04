import React from 'react';
import {
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSessions } from '@/api/hooks/useSessions';
import type { Session } from '@/types/api';

function getSessionTypeIcon(type: string): string {
  const icons: Record<string, string> = {
    running: 'R',
    cycling: 'C',
    strength: 'S',
    football: 'F',
    swimming: 'W',
    other: 'O',
  };
  return icons[type.toLowerCase()] ?? type.charAt(0).toUpperCase();
}

function getSourceColor(source: string): string {
  return source === 'garmin' ? '#6366f1' : '#6b7280';
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function SessionItem({ session }: { session: Session }) {
  const [expanded, setExpanded] = React.useState(false);

  return (
    <Pressable
      style={styles.sessionItem}
      onPress={() => setExpanded(!expanded)}
      testID={`session-${session.id}`}
    >
      <View style={styles.sessionHeader}>
        <View style={styles.sessionTypeIcon}>
          <Text style={styles.sessionTypeText}>
            {getSessionTypeIcon(session.session_type)}
          </Text>
        </View>
        <View style={styles.sessionInfo}>
          <Text style={styles.sessionType}>{session.session_type}</Text>
          <Text style={styles.sessionDate}>
            {formatDate(session.start_time)}
          </Text>
        </View>
        <View style={styles.sessionMeta}>
          <View
            style={[
              styles.sourceBadge,
              { backgroundColor: getSourceColor(session.source) },
            ]}
          >
            <Text style={styles.sourceBadgeText} testID={`source-${session.id}`}>
              {session.source}
            </Text>
          </View>
          <Text style={styles.sessionDuration}>
            {formatDuration(session.duration_minutes)}
          </Text>
        </View>
      </View>
      {expanded && (
        <View style={styles.sessionDetails} testID={`details-${session.id}`}>
          {session.hr_avg != null && (
            <Text style={styles.detailText}>
              Avg HR: {Math.round(session.hr_avg)} bpm
            </Text>
          )}
          {session.hr_max != null && (
            <Text style={styles.detailText}>
              Max HR: {Math.round(session.hr_max)} bpm
            </Text>
          )}
          {session.distance_meters != null && (
            <Text style={styles.detailText}>
              Distance: {(session.distance_meters / 1000).toFixed(1)} km
            </Text>
          )}
          {session.calories != null && (
            <Text style={styles.detailText}>
              Calories: {session.calories} kcal
            </Text>
          )}
          {session.hr_avg == null &&
            session.distance_meters == null &&
            session.calories == null && (
              <Text style={styles.detailText}>No additional details</Text>
            )}
        </View>
      )}
    </Pressable>
  );
}

export function SessionHistoryScreen() {
  const sessions = useSessions();

  return (
    <View style={styles.container}>
      <FlatList
        data={sessions.data ?? []}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <SessionItem session={item} />}
        contentContainerStyle={styles.listContent}
        refreshing={sessions.isLoading}
        onRefresh={() => sessions.refetch()}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>
              {sessions.isLoading
                ? 'Loading sessions...'
                : 'No sessions found'}
            </Text>
          </View>
        }
        testID="session-list"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  listContent: {
    padding: 16,
    gap: 12,
  },
  sessionItem: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  sessionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  sessionTypeIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#e0e7ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sessionTypeText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#4338ca',
  },
  sessionInfo: {
    flex: 1,
  },
  sessionType: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    textTransform: 'capitalize',
  },
  sessionDate: {
    fontSize: 13,
    color: '#6b7280',
    marginTop: 2,
  },
  sessionMeta: {
    alignItems: 'flex-end',
    gap: 4,
  },
  sourceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  sourceBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#fff',
    textTransform: 'capitalize',
  },
  sessionDuration: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  sessionDetails: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    gap: 4,
  },
  detailText: {
    fontSize: 14,
    color: '#374151',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyText: {
    fontSize: 16,
    color: '#9ca3af',
  },
});
