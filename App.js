import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';


export default function App() {
  return (
    <View style={styles.container}>
      <View style={styles.container1}>

        {/* Header */}
        <View style = {styles.headerContainer}>
          <View style = {styles.MenuButtonContainer}>
            <TouchableOpacity style={styles.MenuButton}>
              <View style={styles.linea} />
              <View style={styles.linea} />
              <View style={styles.linea} />
            </TouchableOpacity>
          </View>
          <View style = {styles.TextContainer}>
            <Text style = {styles.headerText}>
              RummiApp
            </Text>
          </View>
        </View>

        {/* Month and Days */}
        <View style = {styles.month}>
          <View style = {styles.MonthNameContainer}>
            <Text style = {styles.monthText}>
              Junio
            </Text>
          </View>

          <View style = {styles.WeekDayTextContainer}>
            <Text style = {styles.dayText}>
              Lunes
            </Text>
            <Text style = {styles.dayText}>
              Martes
            </Text>
            <Text style = {styles.dayText}>
              Miércoles
            </Text>
            <Text style = {styles.dayText}>
              Jueves
            </Text>
            <Text style = {styles.dayText}>
              Viernes
            </Text>
            <Text style = {styles.dayText}>
              Sábado
            </Text>
            <Text style = {styles.dayText}>
              Domingo
            </Text>
          </View>
          
          {/* Days of the month */}
          <View style = {styles.dayTextContainer}>
            <Text style = {styles.dayText}>
              1
            </Text>
            <Text style = {styles.dayText}>
              2
            </Text>
            <Text style = {styles.dayText}>
              3
            </Text>
            <Text style = {styles.dayText}>
              4
            </Text>
            <Text style = {styles.dayText}>
              5
            </Text>
            <Text style = {styles.dayText}>
              6
            </Text>
            <Text style = {styles.dayText}>
              7
            </Text>
          </View>
        </View>
    </View>
      <View style = {styles.container2}>

        {/* Daily Tasks */}
        <View style = {styles.dailyTasksContainer}>
          <View style = {styles.dailyTasksTextContainer}>
            <Text style = {styles.dailyTasksText}>
              Tareas del día de hoy
            </Text>
            <View style = {styles.dailyTasksPendientesContainer}>
              <Text style = {styles.dailyTasksPendientesText}>
                Pendientes
              </Text>
              </View>
          </View>
        </View>

        {/* Buttons */}
        <View style = {styles.buttonsContainer}>
          <TouchableOpacity style={styles.boton}/>
          <TouchableOpacity style={styles.boton}/>
          </View>
      </View>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({

  // Main Containers
  container: {
    flex: 1,
    backgroundColor: '#fff',
    gap: 60,
  },

  container1: {
    flex: 1,
    backgroundColor: '#f0ff33',
    gap:25,
  },

  container2: {
    flex: 2,
    backgroundColor: '#ff5733',
    gap:20,
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

    headerText: { 
      fontSize: 24,
      fontWeight: 'bold',
    },

  // Calendario Containers

  month: {
    flex: 1,
    backgroundColor: '#fff',
    gap: 15,
  },

  MonthNameContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignContent: 'center',
  },

  WeekDayTextContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },

  dayTextContainer: { 
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 10,
  },


  //Containers del segundo container

  dailyTasksContainer: {
    flex: 1,
      backgroundColor: '#fff',
    },
  buttonsContainer: {
    flex: 1,
    backgroundColor: '#B8F574',
    flexDirection: 'row',
    justifyContent: 'space-around',
  },

  dailyTasksTextContainer: {
    flex: 1,  
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#B8F574',
  },

  //Botones

  MenuButton: {
    justifyContent: 'center',
    alignItems: 'center',
  },

  linea: {
    width: 30,
    height: 2,
    backgroundColor: 'black',
    marginVertical: 2,
    borderRadius: 2,
  },

  boton: {
    width: 20,
    height: 20,
    backgroundColor: '#fff',
  },

});
