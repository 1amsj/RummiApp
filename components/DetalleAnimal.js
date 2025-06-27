// components/DetalleAnimal.js
import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';

export default function DetalleAnimal({ route }) {
  const { animal } = route.params;
  const navigation = useNavigation();

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* Header con botón de menú */}
      <View style={styles.headerContainer}>
        <TouchableOpacity
          style={styles.MenuButton}
          onPress={() => navigation.openDrawer()}
        >
          <View style={styles.linea} />
          <View style={styles.linea} />
          <View style={styles.linea} />
        </TouchableOpacity>
        <Text style={styles.title}>Detalles de {animal.nombre}</Text>
      </View>

      {/* Detalles */}
      <Text style={styles.section}>Raza: <Text style={styles.text}>{animal.raza}</Text></Text>
      <Text style={styles.section}>Estado de salud: <Text style={styles.text}>{animal.estadoSalud}</Text></Text>

      <Text style={styles.section}>Vacunas:</Text>
      {animal.vacunas?.length ? animal.vacunas.map((vac, idx) => (
        <Text key={idx} style={styles.text}>• {vac}</Text>
      )) : <Text style={styles.text}>No hay vacunas registradas</Text>}

      <Text style={styles.section}>Tratamientos pendientes:</Text>
      {animal.tratamientos?.length ? animal.tratamientos.map((trat, idx) => (
        <Text key={idx} style={styles.text}>• {trat}</Text>
      )) : <Text style={styles.text}>No hay tratamientos pendientes</Text>}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: '#E9FDD0',
    flexGrow: 1,
  },
  headerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#B8F574',
    padding: 10,
    marginBottom: 20,
  },
  MenuButton: {
    marginRight: 15,
  },
  linea: {
    width: 30,
    height: 2,
    backgroundColor: 'black',
    marginVertical: 2,
    borderRadius: 2,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
  },
  section: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 15,
  },
  text: {
    fontSize: 16,
    color: '#333',
    marginLeft: 10,
    marginTop: 5,
  },
});
