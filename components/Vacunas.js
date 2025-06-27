import { StatusBar } from 'expo-status-bar';
import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View, TextInput } from 'react-native';
import { Image } from 'react-native';

export default function Vacunas(){
    return(
        <View style = {styles.container}>
            <View style={styles.container1}>
                    {/* Header */}
                <View style={styles.headerContainer}>
                    <TouchableOpacity style={styles.MenuButton} onPress={() => navigation.openDrawer()}>
                        <View style={styles.linea} />
                        <View style={styles.linea} />
                        <View style={styles.linea} />
                    </TouchableOpacity>
                      <View style={styles.TextContainer}>
                        <Text style={styles.headerText}>
                          RummiApp
                        </Text>
                      </View>
                    </View>
                </View>
            <StatusBar style = "auto"/>
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
    gap: 25,
  },
  container2: {
    flex: 2,
    backgroundColor: '#fff',
    gap: 20,
  },
});