import { StatusBar } from 'expo-status-bar';
import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View, TextInput,ScrollView } from 'react-native';
import { Image } from 'react-native';
import Vacunas from './Vacunas'; 

export default function App({ navigation }) {
    return(
        <ScrollView style = {styles.scrollView}>
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
                            Agregar Animal
                        </Text>
                    </View>
                </View>
            </View>

            <View style={styles.container2}>
                <View style ={styles.AddAnimalContainer}>
                    <View style = {styles.NameContainer}>
                        <View style={styles.TitleNameContainer}>
                            <Text style = {styles.NameheaderText}>Nombre del Animal</Text> 
                        </View>
                        <View style={styles.InputNameContainer}>
                            <TextInput style={styles.input} placeholder="Ingrese el nombre del animal"/>
                        </View>
                    </View>
                    <View style = {styles.RazaContainer}>
                        <View style={styles.TitleRazaContainer}>
                            <Text style = {styles.RazaheaderText}>Raza</Text> 
                        </View>
                        <View style={styles.InputRazaContainer}>
                            <TextInput style={styles.input} placeholder="Ingrese la raza del animal"/>
                        </View>
                    </View>
                    <View style = {styles.BornDateContainer}>
                        <View style={styles.TitleBornDateContainer}>
                            <Text style = {styles.BornDateheaderText}>Fecha de Nacimiento</Text> 
                        </View>
                        <View style={styles.InputBornDateContainer}>
                            <TextInput style={styles.input} placeholder="Ingrese la fecha de nacimiento del animal"/>
                        </View>   
                    </View>
                    <View style = {styles.EstadoDeSaludContainer}>
                        <View style={styles.TitleEstadoDeSaludContainer}>
                            <Text style = {styles.EstadoDeSaludheaderText}>Estado de Salud</Text> 
                        </View>
                        <View style={styles.InputEstadoDeSaludContainer}>
                            <TextInput style={styles.input} placeholder="Ingrese el estado de salud del animal"/>
                        </View>
                    </View>
                    <View style={styles.TitleVacunasContainer}>
                        <Text style={styles.VacunasheaderText}>Vacunas</Text>
                        <Vacunas />
                    </View>
                    <View style = {styles.AddButtonContainer}>
                        <TouchableOpacity style = {styles.AddButton}>
                            <Image source={require('../assets/agregar1.png')} style={styles.taskButtonImage} />
                        </TouchableOpacity>
                    </View>
                </View>
            </View>
            <StatusBar style="auto" />
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
    headerText: {
        fontSize: 24,
        fontWeight: 'bold',
    },
    VacunasheaderText: {
        marginBottom: 10,
    },

    //Input Styles
    input: {
        width: '90%',
        height: 50,
        backgroundColor: 'rgba(255, 255, 255, 0.5)',
        borderRadius: 10,
        paddingHorizontal: 10,
        fontSize: 16,
    },
    VacunaInput: {
        width: '90%',
        height: 50,
        backgroundColor: 'rgba(255, 255, 255, 0.5)',
        borderRadius: 10,
        padding: 5,
        paddingHorizontal: 10,
        fontSize: 16,
        flexDirection: 'row',
        justifyContent: 'space-between',
    },

    //Containers

    AddAnimalContainer: {
        flex: 1,
        backgroundColor: 'rgba(184, 245, 116, 0.5)',
        padding: 20,
        borderRadius: 20,
        width: '90%',
        height: '70%',
        gap:25,
    },
    NameContainer: { gap: 15, },
    RazaContainer: { gap: 15,},
    BornDateContainer: { gap: 15, },
    EstadoDeSaludContainer: { gap: 15, },

    //Button
        AddButton: {
        flexDirection: 'row',
        backgroundColor: '#B8F574',
        justifyContent: 'center',
        alignItems: 'center',
        alignSelf: 'center',
        padding: 5,
        borderRadius: 70,
        gap: 10,
        elevation: 6,
    },

    taskButtonImage: {
        width: 40,
        height: 40,
    },
});