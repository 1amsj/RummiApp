import { StatusBar } from 'expo-status-bar';
import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View, TextInput } from 'react-native';
import { Image } from 'react-native';

export default function App() {
    return(
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
                            Agregar Animal
                        </Text>
                    </View>
                </View>
            </View>

            <View style={styles.container2}>
                <View style ={styles.AddAnimalContainer}>
                    
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
        backgroundColor: '#2b893f',
        gap: 25,
    },

    container2: {
        flex: 4,
        backgroundColor: '#632b89',
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
  
});