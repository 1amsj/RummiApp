import { StatusBar } from 'expo-status-bar';
import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, TouchableOpacity, View, TextInput, ScrollView } from 'react-native';
import { Image } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function App({ navigation }) {
  const [searchText, setSearchText] = useState('');
  const [error, setError] = useState('');
  const [animales, setAnimales] = useState([]);
  const [filteredAnimales, setFilteredAnimales] = useState([]);

  // Función para cargar animales desde AsyncStorage
  const cargarAnimales = async () => {
    try {
      const almacenados = await AsyncStorage.getItem('animales');
      const lista = almacenados ? JSON.parse(almacenados) : [];
      setAnimales(lista);
    } catch (error) {
      console.error('Error cargando animales:', error);
    }
  };

  // Se ejecuta al montar y cada 60 segundos para refrescar la lista
  useEffect(() => {
    cargarAnimales();

    const interval = setInterval(() => {
      cargarAnimales();
    }, 60); // 60000 ms = 60 segundos

    return () => clearInterval(interval);
  }, []);

  // Cada vez que cambien animales o searchText se actualiza el filtro
  useEffect(() => {
    if (searchText.trim() === '') {
      setFilteredAnimales(animales);
      setError('');
      return;
    }

    // Validación de texto
    let tieneNumero = false, tieneEspecial = false;
    for (let i = 0; i < searchText.length; i++) {
      const char = searchText[i];
      if (/[0-9]/.test(char)) tieneNumero = true;
      else if (/[^a-zA-Z0-9 ]/.test(char)) tieneEspecial = true;
    }

    if (tieneNumero) {
      setError('No debe incluir números');
      setFilteredAnimales([]);
      return;
    }
    if (tieneEspecial) {
      setError('No incluir caracteres especiales');
      setFilteredAnimales([]);
      return;
    }

    setError('');

    const filtro = animales.filter((animal) =>
      animal.nombre.toLowerCase().includes(searchText.toLowerCase())
    );
    setFilteredAnimales(filtro);
  }, [searchText, animales]);

  // Actualiza solo el texto del filtro
  const validarBusqueda = (texto) => {
    setSearchText(texto);
  };

    return (
        <View style={styles.container}>
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
                            Listado
                        </Text>
                    </View>
                </View>
                <View style={styles.container2}>
                    <View style={styles.ListadoContainer}>
                        <View style={styles.SuperiorContainer}>
                            <View style={styles.CowContainer}>
                                <Image source={require('../assets/vaca.png')} style={styles.Imagen} />
                            </View>
                            <View style={styles.SearchContainer}>
                                <View style={styles.SearchInputContainer}>
                                    <TextInput style={styles.searchInput} placeholder="Buscar..." value={searchText} onChangeText={validarBusqueda} />
                                    {error !== '' && <Text style={styles.errorText}>{error}</Text>}
                                </View>
                                <View style={styles.SearchButtonContainer}>
                                    <TouchableOpacity style={styles.SearchButton}>
                                        <Text style={styles.SearchButtonText}>Buscar</Text>
                                    </TouchableOpacity>
                                </View>
                            </View>
                        </View>
                        <View style={styles.DataNameContainer}>
                            <Text style={styles.DataNameText}>Nombre</Text>
                            <Text style={styles.DataNameText}>Raza</Text>
                            <Text style={styles.DataNameText}>Edad</Text>
                            <Text style={styles.DataNameText}>Estado de salud</Text>
                        </View>
                        <View style={styles.DataContainer}>
                            <View style={styles.Data1Container}>
                                <Text style={styles.DataText}> Bessie</Text>
                            </View>
                            <View style={styles.Data1Container}>
                                <Text style={styles.DataText}>Holstein</Text>
                            </View>
                            <View style={styles.Data1Container}>
                                <Text style={styles.DataText}>5 años</Text>
                            </View>
                            <View style={styles.Data1Container}>
                                <Text style={styles.DataText}>Saludable</Text>
                            </View>

                            <View style={styles.Data1Container}>
                                <Text style={styles.DataText}>Vaca 2</Text>
                            </View>
                            <View style={styles.Data1Container}>
                                <Text style={styles.DataText}>Jersey</Text>
                            </View>
                            <View style={styles.Data1Container}>
                                <Text style={styles.DataText}>4 años</Text>
                            </View>
                            <View style={styles.Data1Container}>
                                <Text style={styles.DataText}>Enferma</Text>
                            </View>
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
        gap: 25,
    },

    container2: {
        flex: 4,
        gap: 20,
        alignContent: 'center',
        alignItems: 'center',
        padding: 15,
        paddingBottom: 50,
    },

    //container del header 
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

    DataNameText: {
        fontSize: 18,
        fontWeight: 'bold',
        width: '20%',
        textAlign: 'center',
    },

    DataText: {
        fontSize: 16,
        color: '#000',
    },

    // Container del listado

    ListadoContainer: {
        flex: 1,
        backgroundColor: 'rgba(184, 245, 116, 0.5)',
        padding: 20,
        borderRadius: 10,
        gap: 20,
        width: '90%',
        height: '70%',
    },

    SuperiorContainer: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 20,
    },

    DataNameContainer: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },

    DataContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
    },

    Data1Container: {
        width: '25%',
        paddingVertical: 5,
        alignItems: 'center',
    },

    //Parte superior del listado

    SearchContainer: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },

    Imagen: {
        width: 50,
        height: 50,
    },

    SearchInputContainer: {
        width: '70%',
    },

    searchInput: {
        backgroundColor: 'rgba(255, 255, 255, 0.5)',
        flex: 1,
        padding: 10,
        borderRadius: 10,
        fontSize: 16,
    },

    SearchButton: {
        backgroundColor: '#B8F574',
        padding: 10,
        borderRadius: 10,
        marginLeft: 10,
    },

    SearchButtonText: {
        fontSize: 16,
        color: '#000',
    },

});
