import React from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useAuthStore } from '@/auth/authStore';
import { useProfile, useUpdateProfile } from '@/api/hooks/useProfile';

export function ProfileScreen() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const profile = useProfile();
  const updateProfile = useUpdateProfile();

  const [position, setPosition] = React.useState('');
  const [heightCm, setHeightCm] = React.useState('');
  const [weightKg, setWeightKg] = React.useState('');
  const [hasChanges, setHasChanges] = React.useState(false);

  React.useEffect(() => {
    if (profile.data) {
      setPosition(profile.data.position ?? '');
      setHeightCm(profile.data.height_cm?.toString() ?? '');
      setWeightKg(profile.data.weight_kg?.toString() ?? '');
    }
  }, [profile.data]);

  const handleFieldChange = (
    setter: (v: string) => void,
    value: string,
  ) => {
    setter(value);
    setHasChanges(true);
  };

  const handleSave = () => {
    const height = heightCm ? parseFloat(heightCm) : null;
    const weight = weightKg ? parseFloat(weightKg) : null;

    if (heightCm && (isNaN(height!) || height! <= 0)) {
      Alert.alert('Invalid Input', 'Please enter a valid height.');
      return;
    }
    if (weightKg && (isNaN(weight!) || weight! <= 0)) {
      Alert.alert('Invalid Input', 'Please enter a valid weight.');
      return;
    }

    updateProfile.mutate(
      {
        position: position || null,
        height_cm: height,
        weight_kg: weight,
      },
      {
        onSuccess: () => {
          setHasChanges(false);
          Alert.alert('Success', 'Profile updated.');
        },
        onError: () => {
          Alert.alert('Error', 'Failed to update profile.');
        },
      },
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.name}>{user?.full_name ?? 'Athlete'}</Text>
        <Text style={styles.email}>{user?.email ?? ''}</Text>
        <Text style={styles.role}>{user?.role ?? ''}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Profile Details</Text>

        <View style={styles.fieldContainer}>
          <Text style={styles.fieldLabel}>Position</Text>
          <TextInput
            style={styles.textInput}
            value={position}
            onChangeText={(v) => handleFieldChange(setPosition, v)}
            placeholder="e.g., Midfielder"
            testID="position-input"
          />
        </View>

        <View style={styles.fieldContainer}>
          <Text style={styles.fieldLabel}>Height (cm)</Text>
          <TextInput
            style={styles.textInput}
            value={heightCm}
            onChangeText={(v) => handleFieldChange(setHeightCm, v)}
            placeholder="e.g., 180"
            keyboardType="numeric"
            testID="height-input"
          />
        </View>

        <View style={styles.fieldContainer}>
          <Text style={styles.fieldLabel}>Weight (kg)</Text>
          <TextInput
            style={styles.textInput}
            value={weightKg}
            onChangeText={(v) => handleFieldChange(setWeightKg, v)}
            placeholder="e.g., 75"
            keyboardType="numeric"
            testID="weight-input"
          />
        </View>

        {hasChanges && (
          <Pressable
            style={[
              styles.saveButton,
              updateProfile.isPending && styles.saveButtonDisabled,
            ]}
            onPress={handleSave}
            disabled={updateProfile.isPending}
            testID="save-button"
          >
            <Text style={styles.saveButtonText}>
              {updateProfile.isPending ? 'Saving...' : 'Save Changes'}
            </Text>
          </Pressable>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Health Connect</Text>
        <View style={styles.garminStatus}>
          <View
            style={[
              styles.statusDot,
              {
                backgroundColor: profile.data?.health_connect_connected
                  ? '#22c55e'
                  : '#ef4444',
              },
            ]}
          />
          <Text style={styles.statusText} testID="health-connect-status">
            {profile.data?.health_connect_connected ? 'Connected' : 'Not Connected'}
          </Text>
        </View>
        {profile.data?.last_sync_at && (
          <Text style={styles.lastSync}>
            Last sync: {new Date(profile.data.last_sync_at).toLocaleString()}
          </Text>
        )}
      </View>

      <Pressable
        style={styles.logoutButton}
        onPress={logout}
        testID="logout-button"
      >
        <Text style={styles.logoutText}>Sign Out</Text>
      </Pressable>
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
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 32,
  },
  name: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  email: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 4,
  },
  role: {
    fontSize: 14,
    color: '#9ca3af',
    textTransform: 'capitalize',
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  fieldContainer: {
    marginBottom: 16,
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 6,
  },
  textInput: {
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    color: '#111827',
  },
  saveButton: {
    height: 44,
    backgroundColor: '#2563eb',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 4,
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  garminStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  statusText: {
    fontSize: 16,
    color: '#374151',
  },
  lastSync: {
    fontSize: 13,
    color: '#6b7280',
    marginTop: 8,
  },
  logoutButton: {
    height: 48,
    backgroundColor: '#ef4444',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  logoutText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
