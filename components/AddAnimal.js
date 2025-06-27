import { StatusBar } from 'expo-status-bar';
import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View, TextInput, ScrollView } from 'react-native';
import { Image } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Vacunas from './Vacunas';

export default function App({ navigation }) {
    const [NameText, setNameText] = useState('');
    const [RazaText, setRazaText] = useState('');
    const [SaludText, setSaludText] = useState('');
    const [fecha, setFecha] = useState('');

    //mensaje error
    const [error, setError] = useState('');
    const [error1, setError1] = useState('');
    const [error2, setError2] = useState('');
    const [error3, setError3] = useState('');

    let tieneNumero = false, tieneEspecial = false;

    const validarNombre = (texto) => {
        setNameText(texto);

        tieneNumero = false; tieneEspecial = false;  // reset cada vez que validas
        for (let i = 0; i < texto.length; i++) {
            const char = texto[i];
            if (/[0-9]/.test(char)) tieneNumero = true;
            else if (/[^a-zA-Z0-9]/.test(char)) tieneEspecial = true;
        }

        if (texto.trim() === '') {
            setError('El nombre no puede estar vacío');
            return;
        }
        if (tieneNumero) {
            setError('No debe incluir números');
            return;
        }
        if (tieneEspecial) {
            setError('No incluir caracteres especiales');
            return;
        }
        setError('');
    };

    const validarRaza = (texto) => {
        setRazaText(texto);

        tieneNumero = false; tieneEspecial = false;
        for (let i = 0; i < texto.length; i++) {
            const char = texto[i];
            if (/[0-9]/.test(char)) tieneNumero = true;
            else if (/[^a-zA-Z0-9]/.test(char)) tieneEspecial = true;
        }

        if (texto.trim() === '') {
            setError1('El nombre no puede estar vacío');
            return;
        }
        if (tieneNumero) {
            setError1('No debe incluir números');
            return;
        }
        if (tieneEspecial) {
            setError1('No incluir caracteres especiales');
            return;
        }
        setError1('');
    };

    const validarFecha = (texto) => {
        setFecha(texto);

        if (texto.trim() === '') {
            setError2('La fecha no puede estar vacía');
            return;
        }

        if (texto.length !== 8) {
            setError2('La fecha debe tener el formato dd/mm/aa');
            return;
        }

        if (texto[2] !== '/' || texto[5] !== '/') {
            setError2('Usa el formato dd/mm/aa con “/”');
            return;
        }

        const diaStr = texto.substring(0, 2);
        const mesStr = texto.substring(3, 5);
        const anioStr = texto.substring(6, 8);

        if (
            isNaN(diaStr) || isNaN(mesStr) || isNaN(anioStr) ||
            !/^\d+$/.test(diaStr) || !/^\d+$/.test(mesStr) || !/^\d+$/.test(anioStr)
        ) {
            setError2('La fecha solo debe contener números');
            return;
        }

        const dia = parseInt(diaStr);
        const mes = parseInt(mesStr);
        const anio = parseInt(anioStr);

        if (dia < 1 || dia > 31) {
            setError2('Día inválido (1–31)');
            return;
        }

        if (mes < 1 || mes > 12) {
            setError2('Mes inválido (1–12)');
            return;
        }

        setError2('');
    };

    const validarSalud = (texto) => {
        setSaludText(texto);

        tieneNumero = false; tieneEspecial = false;
        for (let i = 0; i < texto.length; i++) {
            const char = texto[i];
            if (/[0-9]/.test(char)) tieneNumero = true;
            else if (/[^a-zA-Z0-9]/.test(char)) tieneEspecial = true;
        }

        if (texto.trim() === '') {
            setError3('El nombre no puede estar vacío');
            return;
        }
        if (tieneNumero) {
            setError3('No debe incluir números');
            return;
        }
        if (tieneEspecial) {
            setError3('No incluir caracteres especiales');
            return;
        }
        setError3('');
    };

    // NUEVA función para guardar en AsyncStorage
    const guardarAnimal = async () => {
        if (
            error || error1 || error2 || error3 ||
            !NameText.trim() || !RazaText.trim() || !SaludText.trim() || !fecha.trim()
        ) {
            alert('Por favor corrige los errores antes de guardar.');
            return;
        }
        try {
            const almacenados = await AsyncStorage.getItem('animales');
            const listaAnimales = almacenados ? JSON.parse(almacenados) : [];

            const nuevoAnimal = {
                id: Date.now().toString(),
                nombre: NameText,
                raza: RazaText,
                fechaNacimiento: fecha,
                estadoSalud: SaludText,
            };

            await AsyncStorage.setItem('animales', JSON.stringify([...listaAnimales, nuevoAnimal]));

            // Limpiar campos
            setNameText('');
            setRazaText('');
            setFecha('');
            setSaludText('');
            setError('');
            setError1('');
            setError2('');
            setError3('');

           
        } catch (e) {
            console.log('Error guardando animal:', e);
      
        }
    };

    return (
        <ScrollView>
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
                            <Text style={styles.titleText}>Agregar Animal</Text>
                        </View>
                    </View>
                </View>

                <View style={styles.container2}>
                    <View style={styles.AddAnimalContainer}>
                        <View style={styles.NameContainer}>
                            <View style={styles.TitleNameContainer}>
                                <Text style={styles.headerText}>Nombre del Animal</Text>
                            </View>
                            <View style={styles.InputNameContainer}>
                                <TextInput
                                    style={styles.input}
                                    placeholder="Ingrese el nombre del animal"
                                    value={NameText}
                                    onChangeText={validarNombre}
                                />
                                {error !== '' && <Text style={styles.errorText}>{error}</Text>}
                            </View>
                        </View>

                        <View style={styles.RazaContainer}>
                            <View style={styles.TitleRazaContainer}>
                                <Text style={styles.headerText}>Raza</Text>
                            </View>
                            <View style={styles.InputRazaContainer}>
                                <TextInput
                                    style={styles.input}
                                    placeholder="Ingrese la raza del animal"
                                    value={RazaText}
                                    onChangeText={validarRaza}
                                />
                                {error1 !== '' && <Text style={styles.errorText}>{error1}</Text>}
                            </View>
                        </View>

                        <View style={styles.BornDateContainer}>
                            <View style={styles.TitleBornDateContainer}>
                                <Text style={styles.headerText}>Fecha de Nacimiento</Text>
                            </View>
                            <View style={styles.InputBornDateContainer}>
                                <TextInput
                                    style={styles.input}
                                    placeholder="DD/MM/AA"
                                    maxLength={8}
                                    value={fecha}
                                    onChangeText={validarFecha}
                                />
                                {error2 !== '' && <Text style={styles.errorText}>{error2}</Text>}
                            </View>
                        </View>

                        <View style={styles.EstadoDeSaludContainer}>
                            <View style={styles.TitleEstadoDeSaludContainer}>
                                <Text style={styles.headerText}>Estado de Salud</Text>
                            </View>
                            <View style={styles.InputEstadoDeSaludContainer}>
                                <TextInput
                                    style={styles.input}
                                    placeholder="Ingrese el estado de salud del animal"
                                    value={SaludText}
                                    onChangeText={validarSalud}
                                />
                                {error3 !== '' && <Text style={styles.errorText}>{error3}</Text>}
                            </View>
                        </View>

                        <View style={styles.TitleVacunasContainer}>
                            <Text style={styles.VacunasHeaderText}>Vacunas</Text>
                            <Vacunas />
                        </View>

                        <View style={styles.AddButtonContainer}>
                            <TouchableOpacity style={styles.AddButton} onPress={guardarAnimal}>
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
        gap: 20,
        alignContent: 'center',
        alignItems: 'center',
        padding: 15,
        paddingBottom: 50,
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
    titleText: {
        fontSize: 20,
        fontWeight: 'bold',
    },
    VacunasHeaderText: {
        marginBottom: 10,
        fontWeight: 'bold',
        fontSize: 18,
    },
    headerText: {
        fontSize: 24,
        fontWeight: 'bold',
        fontSize: 18,
    },
    input: {
        width: '90%',
        height: 50,
        backgroundColor: 'rgba(255, 255, 255, 0.5)',
        borderRadius: 10,
        paddingHorizontal: 10,
        fontSize: 16,
    },
    AddAnimalContainer: {
        flex: 1,
        backgroundColor: 'rgba(184, 245, 116, 0.5)',
        padding: 20,
        borderRadius: 20,
        width: '90%',
        height: '70%',
        gap: 25,
    },
    NameContainer: { gap: 15 },
    RazaContainer: { gap: 15 },
    BornDateContainer: { gap: 15 },
    EstadoDeSaludContainer: { gap: 15 },
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
    errorText: {
        color: 'red',
        marginTop: 5,
        fontSize: 14,
    },
});
