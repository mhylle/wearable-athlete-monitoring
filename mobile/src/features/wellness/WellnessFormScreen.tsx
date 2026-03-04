import React from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import {
  useLatestWellness,
  useSubmitWellness,
  useUpdateWellness,
} from '@/api/hooks/useWellness';

const MOOD_LABELS = ['Very Bad', 'Bad', 'OK', 'Good', 'Great'];
const SLEEP_LABELS = ['Very Poor', 'Poor', 'Fair', 'Good', 'Excellent'];

function SliderControl({
  label,
  value,
  min,
  max,
  onChange,
  testID,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (v: number) => void;
  testID: string;
}) {
  return (
    <View style={styles.fieldContainer}>
      <Text style={styles.fieldLabel}>
        {label}: <Text style={styles.fieldValue}>{value}</Text>
      </Text>
      <View style={styles.sliderRow} testID={testID}>
        {Array.from({ length: max - min + 1 }, (_, i) => i + min).map((v) => (
          <Pressable
            key={v}
            onPress={() => onChange(v)}
            style={[
              styles.sliderButton,
              v === value && styles.sliderButtonActive,
            ]}
            testID={`${testID}-${v}`}
          >
            <Text
              style={[
                styles.sliderButtonText,
                v === value && styles.sliderButtonTextActive,
              ]}
            >
              {v}
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

function ButtonGroup({
  label,
  labels,
  value,
  onChange,
  testID,
}: {
  label: string;
  labels: string[];
  value: number;
  onChange: (v: number) => void;
  testID: string;
}) {
  return (
    <View style={styles.fieldContainer}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.buttonGroup} testID={testID}>
        {labels.map((btnLabel, index) => {
          const btnValue = index + 1;
          return (
            <Pressable
              key={btnValue}
              onPress={() => onChange(btnValue)}
              style={[
                styles.groupButton,
                btnValue === value && styles.groupButtonActive,
              ]}
              testID={`${testID}-${btnValue}`}
            >
              <Text
                style={[
                  styles.groupButtonText,
                  btnValue === value && styles.groupButtonTextActive,
                ]}
              >
                {btnLabel}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

export function WellnessFormScreen() {
  const latestWellness = useLatestWellness();
  const submitWellness = useSubmitWellness();
  const updateWellness = useUpdateWellness();

  const [srpe, setSrpe] = React.useState(5);
  const [duration, setDuration] = React.useState('60');
  const [soreness, setSoreness] = React.useState(5);
  const [fatigue, setFatigue] = React.useState(5);
  const [mood, setMood] = React.useState(3);
  const [sleepQuality, setSleepQuality] = React.useState(3);
  const [notes, setNotes] = React.useState('');
  const [isEditing, setIsEditing] = React.useState(false);

  React.useEffect(() => {
    if (latestWellness.data) {
      const entry = latestWellness.data;
      const today = new Date().toISOString().slice(0, 10);
      if (entry.date === today) {
        setSrpe(entry.srpe);
        setDuration(
          entry.session_duration_minutes?.toString() ?? '60',
        );
        setSoreness(entry.soreness);
        setFatigue(entry.fatigue);
        setMood(entry.mood);
        setSleepQuality(entry.sleep_quality);
        setNotes(entry.notes ?? '');
        setIsEditing(true);
      }
    }
  }, [latestWellness.data]);

  const isSubmitting = submitWellness.isPending || updateWellness.isPending;

  const handleSubmit = () => {
    const durationNum = parseInt(duration, 10);
    if (isNaN(durationNum) || durationNum < 0) {
      Alert.alert('Invalid Input', 'Please enter a valid session duration.');
      return;
    }

    const data = {
      srpe,
      session_duration_minutes: durationNum,
      soreness,
      fatigue,
      mood,
      sleep_quality: sleepQuality,
      notes: notes.trim() || undefined,
    };

    if (isEditing && latestWellness.data) {
      updateWellness.mutate(
        { id: latestWellness.data.id, data },
        {
          onSuccess: () => {
            Alert.alert('Success', 'Wellness entry updated.');
          },
          onError: () => {
            Alert.alert('Error', 'Failed to update wellness entry.');
          },
        },
      );
    } else {
      submitWellness.mutate(data, {
        onSuccess: () => {
          Alert.alert('Success', 'Wellness entry submitted.');
          setIsEditing(true);
        },
        onError: () => {
          Alert.alert('Error', 'Failed to submit wellness entry.');
        },
      });
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
      >
        {isEditing && (
          <View style={styles.editBanner}>
            <Text style={styles.editBannerText}>
              Editing today's entry
            </Text>
          </View>
        )}

        <SliderControl
          label="sRPE (Session Rating of Perceived Exertion)"
          value={srpe}
          min={1}
          max={10}
          onChange={setSrpe}
          testID="srpe-slider"
        />

        <View style={styles.fieldContainer}>
          <Text style={styles.fieldLabel}>Session Duration (minutes)</Text>
          <TextInput
            style={styles.textInput}
            value={duration}
            onChangeText={setDuration}
            keyboardType="numeric"
            placeholder="60"
            testID="duration-input"
          />
        </View>

        <SliderControl
          label="Soreness"
          value={soreness}
          min={1}
          max={10}
          onChange={setSoreness}
          testID="soreness-slider"
        />

        <SliderControl
          label="Fatigue"
          value={fatigue}
          min={1}
          max={10}
          onChange={setFatigue}
          testID="fatigue-slider"
        />

        <ButtonGroup
          label="Mood"
          labels={MOOD_LABELS}
          value={mood}
          onChange={setMood}
          testID="mood-picker"
        />

        <ButtonGroup
          label="Sleep Quality"
          labels={SLEEP_LABELS}
          value={sleepQuality}
          onChange={setSleepQuality}
          testID="sleep-quality-picker"
        />

        <View style={styles.fieldContainer}>
          <Text style={styles.fieldLabel}>Notes</Text>
          <TextInput
            style={[styles.textInput, styles.textArea]}
            value={notes}
            onChangeText={setNotes}
            placeholder="Any additional notes..."
            multiline
            numberOfLines={3}
            testID="notes-input"
          />
        </View>

        <Pressable
          style={[styles.submitButton, isSubmitting && styles.submitButtonDisabled]}
          onPress={handleSubmit}
          disabled={isSubmitting}
          testID="submit-button"
        >
          <Text style={styles.submitButtonText}>
            {isSubmitting
              ? 'Submitting...'
              : isEditing
                ? 'Update Entry'
                : 'Submit Entry'}
          </Text>
        </Pressable>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  editBanner: {
    backgroundColor: '#dbeafe',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  editBannerText: {
    fontSize: 14,
    color: '#1e40af',
    fontWeight: '500',
    textAlign: 'center',
  },
  fieldContainer: {
    marginBottom: 20,
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  fieldValue: {
    fontWeight: '700',
    color: '#2563eb',
  },
  sliderRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  sliderButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#e5e7eb',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sliderButtonActive: {
    backgroundColor: '#2563eb',
  },
  sliderButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  sliderButtonTextActive: {
    color: '#fff',
  },
  buttonGroup: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  groupButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#e5e7eb',
  },
  groupButtonActive: {
    backgroundColor: '#2563eb',
  },
  groupButtonText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#374151',
  },
  groupButtonTextActive: {
    color: '#fff',
  },
  textInput: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    color: '#111827',
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  submitButton: {
    height: 48,
    backgroundColor: '#2563eb',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
