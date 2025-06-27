import { StatusBar } from 'expo-status-bar';
import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View, TextInput, ScrollView } from 'react-native';
import { Image } from 'react-native';


export default function Vacunas({ navigation }) {
  return (
    <ScrollView contentContainerStyle={styles.container}>
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
      <StatusBar style="auto" />
    </ScrollView>
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
    headerText:{
        fontSize: 24,
        fontWeight: 'bold',
    },
});