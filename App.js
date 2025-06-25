import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Image } from 'react-native';
import {Listado} from './components/Listado';



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
        <View style = {styles.dailyTasksContainer}> 
          <View style = {styles.dailyTasksTextContainer}> 
            <View style = {styles.dailyTodayAddTasksContainer}> 
              <View style = {styles.dailyTodayTasksContainer}> 
                <Text style = {styles.dailyTasksText}>
                  Tareas del día de hoy
                </Text>
              </View>
              <View style = {styles.dailyAddTasksContainer}> 
                <TouchableOpacity style={styles.boton}>
                  <Image source={require('./assets/agregar1.png')} style={styles.imagen}/>
                </TouchableOpacity>
              </View>
            </View>
            <View style = {styles.dailyTasksPendientesMainContainer}>
              <View style = {styles.dailyTasksPendientesContainer}>
                <View style = {styles.dailyCheckTaskContainer}>
                  <TouchableOpacity style={styles.boton}>
                    <Image source={require('./assets/registro.png')} style={styles.imagen}/>
                  </TouchableOpacity>
                </View>
                <View style = {styles.dailyTasksPendientesTextContainer}>
                  <Text style = {styles.dailyTasksPendientesText}>
                    Vacunar a Raul
                  </Text>
                </View>
              </View>

              <View style = {styles.dailyTasksPendientesContainer}>
                <View style = {styles.dailyCheckTaskContainer}>
                  <TouchableOpacity style={styles.boton}>
                    <Image source={require('./assets/registro.png')} style={styles.imagen}/>
                  </TouchableOpacity>
                </View>
                <View style = {styles.dailyTasksPendientesTextContainer}>
                  <Text style = {styles.dailyTasksPendientesText}>
                    Vacunar Maria
                  </Text>
                </View>
              </View>
            </View>
          </View>
        </View>

        {/* Buttons */}
        <View style = {styles.buttonsContainer}>
          <View style={styles.buttons}>
            <TouchableOpacity style={styles.boton}>
              <Image source={require('./assets/portapapeles.png')} style={styles.imagen}/>
            </TouchableOpacity>
            <TouchableOpacity style={styles.boton}>
              <Image source={require('./assets/calendario.png')} style={styles.imagen}/>
            </TouchableOpacity>
          </View>
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
    backgroundColor: '#fff',
    gap:25,
  },

  container2: {
    flex: 2,
    backgroundColor: '#fff',
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

    // Textos
    dailyTasksText: {
      fontSize: 18,
      fontWeight: 'bold',
    },

    headerText: { 
      fontSize: 24,
      fontWeight: 'bold',
    },

    dailyTasksPendientesText: {
      fontSize: 18,
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


  //Containers del container del botón 

  buttonsContainer: {
    flex: 1,
    backgroundColor: '#fff',
    flexDirection: 'row',
    justifyContent: 'space-around',
  },

  
  buttons: {
    flexDirection: 'row',         
    backgroundColor: '#B8F574', 
    width: '60%',             
    height: 60,   
    justifyContent: 'center',   
    alignItems: 'center',      
    alignSelf: 'center',        
    padding: 15,                
    borderRadius: 40,           
    gap: 40,                    
    elevation: 6,
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
    width: 40,
    height: 40,
    flexDirection: 'row',  
    alignContent: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
  },

  imagen: {
    width: '90%',
    height: '90%',
  },


  //containers de las tareas diarias

    dailyTasksTextContainer: {
    width: '80%',
    flex: 1,  
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#B8F574',
    justifyContent: 'flex-start',
    gap: 10,
    borderRadius: 20,
  },

  
  dailyTasksContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
      
  },
    
  dailyTodayAddTasksContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 3,
    paddingHorizontal: 20,
    gap: 90,
  },

  dailyAddTasksContainer: {
    width: 40,  
    height: 40,
    justifyContent: 'center',   
    alignItems: 'center',
  },

  dailyTasksPendientesContainer: {
    width: '100%',    
    backgroundColor: '#B8F574',
    flexDirection: 'row',
    justifyContent: 'flex-start',
    alignItems: 'center',
    gap: 10,
  },

  dailyTasksPendientesMainContainer: {
    width: '100%',
    backgroundColor: '#B8F574',
    padding: 10
  },

});
