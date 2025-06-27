import React, { useEffect, useState } from "react";
import {
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  Alert,
  ScrollView,
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

      <TextInput
        style={styles.input}
        placeholder="Nombre de tarea"
        value={nombre}
        onChangeText={setNombre}
      />
      <TextInput
        style={styles.input}
        placeholder="Descripción"
        value={descripcion}
        onChangeText={setDescripcion}
      />
      <TouchableOpacity style={styles.button} onPress={guardarTarea}>
        <Text style={styles.buttonText}>Guardar tarea</Text>
      </TouchableOpacity>

      
      {error !== "" && <Text style={styles.error}>{error}</Text>}

      
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: "#fff",
    flexGrow: 1,
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
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 10,
    padding: 10,
    marginBottom: 10,
  },
  button: {
    backgroundColor: "#B8F574",
    padding: 12,
    borderRadius: 10,
    alignItems: "center",
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
});
