import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
  FlatList,
} from 'react-native';

const commonVaccines = [                // Almacena las vacunas como un array de objetos (Base de datos?)
  'Fiebre Aftosa',
  'Carbunco Sintomático',
  'Brucelosis',
  'Rabia',
  'Leptospirosis',
  'Enfermedad Respiratoria Bovina',
  'Mastitis',
];

export default function Vacuna() {              
  const [showVaccines, setShowVaccines] = useState(false);
  const [selectedVaccines, setSelectedVaccines] = useState([]);   // Almacena las vacunas seleccionadas como un array de objetos (Base de datos?)

  const toggleSelection = (vacuna) => {
    if (selectedVaccines.includes(vacuna)) {
      setSelectedVaccines(selectedVaccines.filter((v) => v !== vacuna));
    } else {
      setSelectedVaccines([...selectedVaccines, vacuna]);
    }
  };

  const handleAddVacuna = () => {
    setShowVaccines(true);
  };

  return (
    <View style={styles.vacunaSection}>
      <View style={styles.vacunaHeader}>
        <Text style={styles.headerText}>Agregue una vacuna</Text>
        <TouchableOpacity onPress={handleAddVacuna}>
          <Image
            source={require('../assets/agregar1.png')}
            style={styles.addIcon}
          />
        </TouchableOpacity>
      </View>

      {showVaccines && (
        <View style={styles.vaccineList}>
          {commonVaccines.map((vacuna, index) => {
            const isSelected = selectedVaccines.includes(vacuna);
            return (
              <TouchableOpacity
                key={index}
                style={[
                  styles.vaccineOption,
                  isSelected && styles.selectedOption,
                ]}
                onPress={() => toggleSelection(vacuna)}
              >
                <Text
                  style={{
                    color: isSelected ? '#fff' : '#000',
                    fontWeight: isSelected ? 'bold' : 'normal',
                  }}
                >
                  {vacuna}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      )}

    </View>
  );
}

const styles = StyleSheet.create({
  vacunaSection: {
    marginTop: 10,
  },
  vacunaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerText: {
    fontSize: 16,
  },
  addIcon: {
    width: 30,
    height: 30,
  },
  vaccineList: {
    marginTop: 10,
    backgroundColor: '#eaffda',
    borderRadius: 10,
    padding: 10,
  },
  vaccineOption: {
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#ccc',
    borderRadius: 5,
  },
  selectedOption: {
    backgroundColor: '#B8F574',
  },
});