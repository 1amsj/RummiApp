// ListadoStack.js
import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import Listado from './components/Listado';
import DetalleAnimal from './components/DetalleAnimal';

const Stack = createStackNavigator();

export default function ListadoStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Listado" component={Listado} />
      <Stack.Screen name="DetalleAnimal" component={DetalleAnimal} />
    </Stack.Navigator>
  );
}