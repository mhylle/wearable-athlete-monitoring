import React from 'react';
import { AppRegistry, Text, View } from 'react-native';

function TestApp() {
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' }}>
      <Text style={{ fontSize: 24, color: '#000' }}>Athlete Monitor Works!</Text>
    </View>
  );
}

AppRegistry.registerComponent('main', () => TestApp);
