import React, { useEffect, useState } from 'react';
import {
  StyleSheet, Text, TouchableOpacity, View, Image, ScrollView, Platform
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import WeekView from '../components/WeekView'; // Asegúrate de que la ruta esté bien

export default function MainScreen({ navigation }) {
  const obtenerFechaHoy = () => {
    const hoy = new Date();
    return hoy.toISOString().split('T')[0];
  };

  const [selectedDate, setSelectedDate] = useState(obtenerFechaHoy());
  const [tareasHoy, setTareasHoy] = useState([]);

  const cargarTareasDelDia = async () => {
    const hoy = selectedDate;
    const datos = await AsyncStorage.getItem('tareas');
    if (datos) {
      const tareas = JSON.parse(datos);
      const filtradas = tareas.filter(t => t.fecha === hoy);
      setTareasHoy(filtradas);
    }
  };

  const toggleStatus = async (id) => {
    const datos = await AsyncStorage.getItem('tareas');
    if (datos) {
      let tareas = JSON.parse(datos);
      tareas = tareas.map(t => {
        if (t.id === id) {
          t.status = t.status === 1 ? 0 : 1;
        }
        return t;
      });
      await AsyncStorage.setItem('tareas', JSON.stringify(tareas));
      cargarTareasDelDia();
    }
  };

  useEffect(() => {
    cargarTareasDelDia();
  }, [selectedDate]);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.MenuButton} onPress={() => navigation.openDrawer()}>
          <View style={styles.linea} />
          <View style={styles.linea} />
          <View style={styles.linea} />
        </TouchableOpacity>
        <Text style={styles.headerText}>RummiApp</Text>
      </View>

      {/* Calendario Semanal */}
      <WeekView selectedDate={selectedDate} onSelectDate={setSelectedDate} />

      {/* Contenedor de tareas */}
      <View style={styles.tasksContainer}>
        <View style={styles.tasksHeader}>
          <Text style={styles.tasksTitle}>Tus tareas del día de hoy</Text>
          <TouchableOpacity onPress={() => navigation.navigate('NewTask')}>
            <Image source={require('../assets/agregar1.png')} style={styles.icon} />
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent}>
          {tareasHoy.length === 0 ? (
            <Text style={{ color: '#777', textAlign: 'center', fontFamily: Platform.OS === 'ios' ? 'System' : 'sans-serif' }}>
              No hay tareas para este día
            </Text>
          ) : (
            tareasHoy.map((tarea) => (
              <View key={tarea.id} style={styles.taskItem}>
                <TouchableOpacity onPress={() => toggleStatus(tarea.id)}>
                  <Image
                    source={
                      tarea.status === 1
                        ? require('../assets/lista-de-verificacion.png')
                        : require('../assets/registro.png')
                    }
                    style={styles.icon}
                  />
                </TouchableOpacity>
                <View style={styles.taskTextContainer}>
                  <Text
                    style={[
                      styles.taskTitle,
                      tarea.status === 1 && { textDecorationLine: 'line-through', color: '#555' }
                    ]}
                  >
                    {tarea.nombre}
                  </Text>
                  <Text style={styles.taskDesc}>{tarea.descripcion}</Text>
                </View>
              </View>
            ))
          )}
        </ScrollView>
      </View>

      {/* Botones inferiores */}
      <View style={styles.bottomButtons}>
        <TouchableOpacity onPress={() => navigation.navigate('Listado')}>
          <Image source={require('../assets/portapapeles.png')} style={styles.icon} />
        </TouchableOpacity>
        <TouchableOpacity onPress={() => navigation.navigate('Calendario')}>
          <Image source={require('../assets/calendario.png')} style={styles.icon} />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F4F4F4',
  },
  header: {
    backgroundColor: '#B8F574',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
    gap: 10,
    paddingTop: 50,
  },
  MenuButton: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 8,
  },
  linea: {
    width: 25,
    height: 2,
    backgroundColor: 'black',
    marginVertical: 1.5,
    borderRadius: 1,
  },
  headerText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
    fontFamily: Platform.OS === 'ios' ? 'System' : 'sans-serif',
  },
  tasksContainer: {
    backgroundColor: '#B8F574',
    margin: 20,
    padding: 15,
    borderRadius: 20,
    flex: 1,
  },
  tasksHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  tasksTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
    fontFamily: Platform.OS === 'ios' ? 'System' : 'sans-serif',
  },
  scrollContent: {
    gap: 12,
  },
  taskItem: {
    backgroundColor: '#D7F9A3',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    borderRadius: 12,
    gap: 10,
  },
  taskTextContainer: {
    flex: 1,
  },
  taskTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
    fontFamily: Platform.OS === 'ios' ? 'System' : 'sans-serif',
  },
  taskDesc: {
    fontSize: 14,
    color: '#555',
    fontFamily: Platform.OS === 'ios' ? 'System' : 'sans-serif',
  },
  icon: {
    width: 24,
    height: 24,
  },
  bottomButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    padding: 10,
    backgroundColor: '#B8F574',
    marginHorizontal: 50,
    marginBottom: 20,
    borderRadius: 30,
  },
});
