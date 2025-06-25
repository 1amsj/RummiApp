import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Image } from 'react-native';

export default function App() {
    return(
        <View style ={styles.container}>
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
                    Listado
                    </Text>
                </View>
            </View>
            <View style = {styles.container2}>
                <View style = {styles.ListadoContainer}>
                    <View style = {styles.SuperiorContainer}>
                        <View style = {styles.CowContainer}>
                        </View>
                        <View style = {styles.SearchContainer}>
                        </View>
                    </View>
                    <View style = {styles.DataNameContainer}>
                        <Text style = {styles.DataNameText}>
                            Nombre
                        </Text>    
                        <Text style = {styles.DataNameText}> 
                            Raza
                        </Text>
                        <Text style = {styles.DataNameText}>
                            Edad
                        </Text>
                        <Text style = {styles.DataNameText}>
                            Estado de salud
                        </Text>
                    </View>
                    <View style = {styles.DataContainer}>
                        <Text style = {styles.DataText}>
                            Bessie
                        </Text>
                        <Text style = {styles.DataText}>
                            Holstein
                        </Text>
                        <Text style = {styles.DataText}>
                            5 años
                        </Text>
                        <Text style = {styles.DataText}>
                            Saludable
                        </Text>
                    </View>
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
    gap: 60,
  },

    container1: {
    flex: 1,
    backgroundColor: '#fff',
    gap:25,
  },

    container2: {
    flex: 3,
    backgroundColor: '#fff',
    gap:20,
  },
  
});