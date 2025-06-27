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
      <View style={styles.container1}>
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
      </View>

      <View style={styles.container2}>
        <View style={styles.DetailsContainer}>
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
        </View>
      </View>

    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    gap: 40,
  },
  container1: {
    flex: 1,
    backgroundColor: '#fff',
    gap: 25,
  },
  container2: {
    flex: 4,
    backgroundColor: '#fff',
    gap: 20,
    alignContent: 'center',
    alignItems: 'center',
    padding: 15,
    paddingBottom: 50,
  },

  DetailsContainer: {
    flex: 1,
    backgroundColor: 'rgba(184, 245, 116, 0.5)',
    padding: 20,
    borderRadius: 20,
    width: '90%',
    height: '70%',
    gap: 25,
    alignContent: 'center',
},
  headerContainer: {
  flexDirection: 'row',
  alignItems: 'center',
  justifyContent: 'flex-start',
  padding: 10,
  gap: 10,
  backgroundColor: '#B8F574',
  height: 130,
},
  TextContainer: {
  paddingLeft: 10,
},
  linea: {
  width: 30,
  height: 2,
  backgroundColor: 'black',
  marginVertical: 2,
  borderRadius: 2,
},
  title: {
  fontSize: 20,
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
