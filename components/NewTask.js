import React, { useEffect, useState } from "react";
import {
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
    Alert,
    ScrollView,
    Image
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Calendar } from "react-native-calendars";

export default function Listado({ navigation }) {
    const [todasLasTareas, setTodasLasTareas] = useState([]);
    const [tareasFiltradas, setTareasFiltradas] = useState([]);
    const [nombre, setNombre] = useState("");
    const [descripcion, setDescripcion] = useState("");
    const [fechaSeleccionada, setFechaSeleccionada] = useState(new Date());
    const [searchText, setSearchText] = useState("");
    const [error, setError] = useState("");
    const [error1, setError1] = useState("");

    useEffect(() => {
        cargarTareas();
    }, []);

    useEffect(() => {
        filtrarTareas();
    }, [fechaSeleccionada, todasLasTareas, searchText]);

    const guardarTarea = async () => {
        if (nombre.trim() === "") {
            Alert.alert("Error", "El nombre no puede estar vacío");
            return;
        }

        const nuevaTarea = {
            id: Date.now(),
            nombre,
            descripcion,
            fecha: fechaSeleccionada.toISOString().split("T")[0],
            status: 0,
        };

        const actualizadas = [...todasLasTareas, nuevaTarea];
        setTodasLasTareas(actualizadas);
        await AsyncStorage.setItem("tareas", JSON.stringify(actualizadas));
        setNombre("");
        setDescripcion("");
    };

    const cargarTareas = async () => {
        const datos = await AsyncStorage.getItem("tareas");
        if (datos) {
            setTodasLasTareas(JSON.parse(datos));
        }
    };

    const filtrarTareas = () => {
        const fechaStr = fechaSeleccionada.toISOString().split("T")[0];
        const filtradas = todasLasTareas.filter(
            (t) =>
                t.fecha === fechaStr &&
                t.nombre.toLowerCase().includes(searchText.toLowerCase())
        );
        setTareasFiltradas(filtradas);
    };

    const validarBusqueda = (texto) => {
        setSearchText(texto);
        if (texto.trim() === "") setError("El nombre no puede estar vacío");
        else if (/\d/.test(texto)) setError("No debe incluir números");
        else if (/[^a-zA-Z\s]/.test(texto))
            setError("No incluir caracteres especiales");
        else setError("");
    };

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <View style={styles.container1}>
                {/* Header con menú */}
                <View style={styles.headerContainer}>
                    <TouchableOpacity
                        style={styles.MenuButton}
                        onPress={() => navigation.openDrawer()}
                    >
                        <View style={styles.linea} />
                        <View style={styles.linea} />
                        <View style={styles.linea} />
                    </TouchableOpacity>
                    <View style={styles.TextContainer}>
                        <Text style={styles.headerText}>Listado de Tareas</Text>
                    </View>
                </View>
            </View>

            <View style={styles.container2}>
                <View style={styles.AddTaskContainer}>
                    <Calendar
                        onDayPress={(day) => setFechaSeleccionada(new Date(day.dateString))}
                        markedDates={{
                            [fechaSeleccionada.toISOString().split("T")[0]]: {
                                selected: true,
                                selectedColor: "#B8F574",
                            },
                        }}
                        theme={{
                            selectedDayBackgroundColor: "#B8F574",
                            arrowColor: "#B8F574",
                        }}
                        style={{ marginBottom: 20 }}
                    />
                    <View style={styles.NameContainer}>
                        <TextInput
                            style={styles.input}
                            placeholder="Nombre de tarea"
                            value={nombre}
                            onChangeText={setNombre}
                            onBlur={() => {
                                const texto1 = nombre.trim();
                                if (texto1 === '') {
                                    setError1("El campo no puede estar vacío");
                                } 
                                if (/\d/.test(texto1)) {
                                    setError1("No debe incluir números");
                                } 
                                if (/[^a-zA-Z\s]/.test(texto1)) {
                                    setError1("No incluir caracteres especiales");
                                } else {
                                    setError1("");
                                }
                            }}
                        />
                        {error1 !== "" && <Text style={styles.error}>{error1}</Text>}
                    </View>



                    <View style={styles.DescriptionContainer}>
                        <TextInput
                            style={styles.input}
                            placeholder="Descripción"
                            value={descripcion}
                            onChangeText={setDescripcion}
                            onBlur={() => {
                                const texto = descripcion.trim();

                                if (texto === '') {
                                    setError("El campo no puede estar vacío");
                                } else if (/\d/.test(texto)) {
                                    setError("No debe incluir números");
                                } else if (/[^a-zA-Z\s]/.test(texto)) {
                                    setError("No incluir caracteres especiales");
                                } else {
                                    setError("");
                                }
                            }}
                        />
                        {error !== "" && <Text style={styles.error}>{error}</Text>}
                    </View>


                    <TouchableOpacity style={styles.button} onPress={guardarTarea}>
                        <Image source={require('../assets/agregar1.png')} style={styles.taskButtonImage} />
                        <Text style={styles.buttonText}>Guardar tarea</Text>
                    </TouchableOpacity>

                </View>

            </View>

        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: "#fff",
        flexGrow: 1,
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
        paddingBottom: 20,
    },
    headerContainer: {
        flexDirection: "row",
        alignItems: "center",
        padding: 10,
        gap: 10,
        backgroundColor: "#B8F574",
        height: 100,
        marginBottom: 20,
    },
    MenuButton: {
        justifyContent: "center",
        alignItems: "center",
    },
    linea: {
        width: 30,
        height: 2,
        backgroundColor: "black",
        marginVertical: 2,
        borderRadius: 2,
    },
    TextContainer: {
        paddingLeft: 10,
    },
    headerText: {
        fontSize: 20,
        fontWeight: "bold",
    },
    title: {
        fontSize: 24,
        fontWeight: "bold",
        marginBottom: 10,
        textAlign: "center",
    },
    input: {
        width: '90%',
        backgroundColor: 'rgba(255, 255, 255, 0.5)',
        borderWidth: 1,
        borderRadius: 10,
        paddingHorizontal: 10,
        fontSize: 16,
    },
    button: {
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
    buttonText: {
        fontSize: 16,
        fontWeight: "bold",
    },
    subtitle: {
        fontSize: 18,
        fontWeight: "bold",
        marginTop: 20,
        marginBottom: 5,
    },
    error: {
        color: "red",
        marginBottom: 10,
    },
    tareaContainer: {
        marginTop: 10,
    },
    tareaItem: {
        backgroundColor: "#eef",
        padding: 10,
        borderRadius: 10,
        marginBottom: 10,
    },
    tareaNombre: {
        fontWeight: "bold",
        fontSize: 16,
    },

    AddTaskContainer: {
        flex: 1,
        backgroundColor: 'rgba(184, 245, 116, 0.5)',
        padding: 20,
        borderRadius: 20,
        width: '90%',
        height: '70%',
        gap: 15,

    },

    taskButtonImage: {
        width: 40,
        height: 40,
    },

});
