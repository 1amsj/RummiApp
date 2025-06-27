import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Platform } from 'react-native';
import { Calendar } from 'react-native-calendars';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function CalendarioTareas({ navigation }) {
  const obtenerFechaHoy = () => {
    const hoy = new Date();
    return hoy.toISOString().split('T')[0]; // formato: YYYY-MM-DD
  };

  const [fechaSeleccionada, setFechaSeleccionada] = useState(obtenerFechaHoy());
  const [tareas, setTareas] = useState([]);

  useEffect(() => {
    obtenerTareas();
  }, [fechaSeleccionada]);

  const obtenerTareas = async () => {
    const todas = await AsyncStorage.getItem('tareas');
    const parsed = todas ? JSON.parse(todas) : [];

    const filtradas = parsed.filter(t => t.fecha === fechaSeleccionada);
    setTareas(filtradas);
  };

  const formatearFechaParaTitulo = (fechaStr) => {
    const [anio, mes, dia] = fechaStr.split('-');
    const meses = [
      'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
      'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
    ];
    return `${parseInt(dia)} de ${meses[parseInt(mes) - 1]} de ${anio}`;
  };

  return (
    <View style={styles.container}>
      {/* Header con menú */}
      <View style={styles.headerContainer}>
        <TouchableOpacity style={styles.MenuButton} onPress={() => navigation.openDrawer()}>
          <View style={styles.linea} />
          <View style={styles.linea} />
          <View style={styles.linea} />
        </TouchableOpacity>
        <View style={styles.TextContainer}>
          <Text style={styles.headerText}>Calendario</Text>
        </View>
      </View>

      {/* Calendario */}
      <Calendar
        onDayPress={(day) => setFechaSeleccionada(day.dateString)}
        markedDates={{
          [fechaSeleccionada]: {
            selected: true,
            selectedColor: '#B8F574',
          },
        }}
        theme={{
          selectedDayBackgroundColor: '#B8F574',
          arrowColor: '#B8F574',
          selectedDayTextColor: 'black',
        }}
        style={{ marginBottom: 20 }}
      />

      {/* Tareas */}
      <View style={styles.tareasContainer}>
        <Text style={styles.tituloTareas}>
          {`Tareas del ${formatearFechaParaTitulo(fechaSeleccionada)}`}
        </Text>
        <ScrollView contentContainerStyle={styles.listaTareas}>
          {tareas.length === 0 ? (
            <Text style={{ color: '#7a7a7a' }}>No hay tareas para esta fecha.</Text>
          ) : (
            tareas.map((tarea) => (
              <View key={tarea.id} style={styles.tareaItem}>
                <Text style={styles.tareaTexto}>• {tarea.nombre}</Text>
                <Text style={styles.descripcionTexto}>{tarea.descripcion}</Text>
              </View>
            ))
          )}
        </ScrollView>
      </View>
    </View>
  );
}


const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    flex: 1,
  },
  headerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#B8F574',
    height: 100,
    paddingHorizontal: 15,
  },
  MenuButton: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 10,
  },
  linea: {
    width: 30,
    height: 2,
    backgroundColor: 'black',
    marginVertical: 2,
    borderRadius: 2,
  },
  TextContainer: {
    marginLeft: 10,
  },
  headerText: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  tareasContainer: {
    margin: 20,
    padding: 20,
    backgroundColor: '#F4FFE4',
    borderRadius: 20,
  },
  tituloTareas: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  listaTareas: {
    gap: 15,
  },
  tareaItem: {
    backgroundColor: '#E9FBD8',
    padding: 10,
    borderRadius: 10,
  },
  tareaTexto: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  descripcionTexto: {
    fontSize: 14,
    color: '#555',
  },
});
