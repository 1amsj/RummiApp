import { StatusBar } from 'expo-status-bar';
import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View, TextInput } from 'react-native';
import { Image } from 'react-native';

export default function App({ navigation }) {
    return (
        <View style={styles.container}>
            <View style={styles.container1}>
                {/* Header */}
                <View style = {styles.headerContainer}>
                    <TouchableOpacity style={styles.MenuButton} onPress={() => navigation.openDrawer()}>
                        <View style={styles.linea} />
                        <View style={styles.linea} />
                        <View style={styles.linea} />
                    </TouchableOpacity>
                    <View style = {styles.TextContainer}>
                        <Text style = {styles.headerText}>
                            Agregar Tareas
                        </Text>
                    </View>
                </View>
            </View>

            <View style={styles.container2}>
                <View style={styles.AddTaskContainer}>
                    <View style={styles.TaskNameInputContainer}>
                        <Text style={styles.TaskNameInputText}>Nombre de la tarea</Text>
                    </View>
                    <View style={styles.TaskInputContainer}>
                        <TextInput style={styles.taskInput} placeholder="Ingrese la tarea" />
                    </View>
                    <View style={styles.TaskDescriptionNameContainer}>
                        <Text style={styles.TaskNameInputText}>Descripción de la tarea</Text>
                    </View>
                    <View style={styles.TaskDescriptionInputContainer}>
                        <TextInput style={styles.taskInput1} placeholder="Ingrese la descripción" />
                    </View>
                    <View style={styles.TaskDateContainer}>
                        <View style={styles.TaskDateTextContainer}>
                            <Text style={styles.TaskNameInputText}>Calendario</Text>
                        </View>
                        <View style={styles.TaskCalendaryContainer}>
                            <TextInput style={styles.taskInput} placeholder="Ingrese la fecha" />
                        </View>
                    </View>
                    <View style={styles.TaskButtonContainer}>
                        <TouchableOpacity style={styles.taskButton}>
                            <Image source={require('../assets/agregar1.png')} style={styles.taskButtonImage} />
                            <Text style={styles.taskButtonText}>Agregar Tarea</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </View>
            <StatusBar style="auto" />
        </View>
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
        gap:20,
        alignContent: 'center', 
        alignItems: 'center',
        padding: 15,
        paddingBottom: 50,
    },

    // Header Styles
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
  
  // texto

    TaskNameInputText: {
        fontSize: 18,
        fontWeight: 'bold',
    },
  
    taskButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },

    headerText: {
    fontSize: 24,
    fontWeight: 'bold',
  },

  //Add task cotainer principal
    AddTaskContainer: {
        flex: 1,
        backgroundColor: 'rgba(184, 245, 116, 0.5)',
        padding: 20,
        borderRadius: 20,
        width: '90%',
        height: '70%',
        gap:25,
        
    },
    taskButton: {
        flexDirection: 'row',
        backgroundColor: '#B8F574',
        width: '70%',
        height: 60,
        justifyContent: 'center',
        alignItems: 'center',
        alignSelf: 'center',
        padding: 15,
        borderRadius: 40,
        gap: 10,
        elevation: 6,
    },

    taskButtonImage: {
        width: 40,
        height: 40,
    },

    taskInput: {
        width: '90%',
        height: 50,
        backgroundColor: 'rgba(255, 255, 255, 0.5)',
        borderWidth: 1,
        borderRadius: 10,
        paddingHorizontal: 10,
        fontSize: 16,
    },

    taskInput1: {
        width: '90%',
        height: 100,
        backgroundColor: 'rgba(255, 255, 255, 0.5)',
        borderWidth: 1,
        borderRadius: 10,
        paddingHorizontal: 10,
        fontSize: 16,
    },

    TaskDateContainer: {
        flexDirection: 'column',
        width: '90%',
        gap: 10,
    },
});

