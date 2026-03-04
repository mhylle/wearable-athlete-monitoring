import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';
import { VitalsScreen } from '@/features/vitals/VitalsScreen';
import { WellnessFormScreen } from '@/features/wellness/WellnessFormScreen';
import { SessionHistoryScreen } from '@/features/sessions/SessionHistoryScreen';
import { ProfileScreen } from '@/features/profile/ProfileScreen';
import { HealthConnectScreen } from '@/features/health-connect/HealthConnectScreen';

const Tab = createBottomTabNavigator();

function TabIcon({ label, focused }: { label: string; focused: boolean }) {
  const icons: Record<string, string> = {
    Vitals: 'V',
    Wellness: 'W',
    Sessions: 'S',
    Health: 'HC',
    Profile: 'P',
  };
  return (
    <Text
      style={{
        fontSize: 18,
        fontWeight: focused ? '700' : '400',
        color: focused ? '#2563eb' : '#9ca3af',
      }}
    >
      {icons[label] ?? label.charAt(0)}
    </Text>
  );
}

export function AppNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused }) => (
          <TabIcon label={route.name} focused={focused} />
        ),
        tabBarActiveTintColor: '#2563eb',
        tabBarInactiveTintColor: '#9ca3af',
        headerStyle: { backgroundColor: '#fff' },
        headerTitleStyle: { fontWeight: '600', color: '#111827' },
      })}
    >
      <Tab.Screen name="Vitals" component={VitalsScreen} />
      <Tab.Screen name="Wellness" component={WellnessFormScreen} />
      <Tab.Screen name="Sessions" component={SessionHistoryScreen} />
      <Tab.Screen name="Health" component={HealthConnectScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}
