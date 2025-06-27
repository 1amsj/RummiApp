import 'react-native-gesture-handler';
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createDrawerNavigator, DrawerContentScrollView } from '@react-navigation/drawer';
import MainScreen from './components/MainScreen';
import Listado from './components/Listado';
import Calendario from './components/Calendario';
import AddAnimal from './components/AddAnimal';
import NewTask from './components/NewTask';
import Vacunas from './components/Vacunas';
import { Text, TouchableOpacity, StyleSheet, View, Image } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

const Drawer = createDrawerNavigator();

// Menú personalizado
function MenuLateral(props) {
  return (
    <DrawerContentScrollView {...props} contentContainerStyle={styles.drawer}>
      <DrawerItem
        label="Inicio"
        imageSource={require('./assets/casa.png')}
        onPress={() => props.navigation.navigate('Inicio')}
      />
      <View style={styles.container}>
        <View style={styles.ImageContainer}>
          <Image source={require('./assets/vaca.png')} style={styles.ImagenStyles} />
        </View>
        <View style={styles.TextContainer}>
          <Text style={styles.sectionTitle}>Gestión de ganado</Text>
        </View>
      </View>

      <DrawerItem
        label="Listado"
        imageSource={require('./assets/portapapeles.png')}
        onPress={() => props.navigation.navigate('Listado')}
      />
      <DrawerItem
        label="Agregar animal"
        imageSource={require('./assets/agregar1.png')}
        onPress={() => props.navigation.navigate('AddAnimal')}
      />
      <View style={styles.container}>
        <View style={styles.ImageContainer}>
          <Image source={require('./assets/agenda.png')} style={styles.ImagenStyles} />
        </View>
        <View style={styles.TextContainer}>
          <Text style={styles.sectionTitle}>Agenda</Text>
        </View>
      </View>
      <DrawerItem
        label="Listado"
        imageSource={require('./assets/calendario.png')}
        onPress={() => props.navigation.navigate('Calendario')}
      />
      <DrawerItem
        label="Agregar tarea"
        imageSource={require('./assets/agregar1.png')}
        onPress={() => props.navigation.navigate('NewTask')}
      />
    </DrawerContentScrollView>
  );
}

function DrawerItem({ label, imageSource, onPress }) {
  return (
    <TouchableOpacity style={styles.item} onPress={onPress}>
      <Image
        source={imageSource}
        style={styles.iconImage}
      />
      <Text style={styles.itemText}>{label}</Text>
    </TouchableOpacity>
  );
}


export default function App() {
  return (
    <NavigationContainer>
      <Drawer.Navigator
        drawerContent={props => <MenuLateral {...props} />}
        screenOptions={{ headerShown: false }}
      >
        <Drawer.Screen name="Inicio" component={MainScreen} />
        <Drawer.Screen name="Listado" component={Listado} />
        <Drawer.Screen name="AddAnimal" component={AddAnimal} />
        <Drawer.Screen name="Calendario" component={Calendario} />
        <Drawer.Screen name="NewTask" component={NewTask} />
      </Drawer.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  drawer: {
    backgroundColor: '#B9F871',
    flex: 1,
    paddingTop: 40,
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingLeft: 20,
  },
  itemText: {
    fontSize: 20,
    color: '#000',
  },
  sectionTitle: {
    fontWeight: 'bold',
    marginTop: 20,
    marginBottom: 8,
    marginLeft: 20,
    color: '#000',
    fontSize: 22,
  },
  screen: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  screenText: {
    fontSize: 24,
    fontWeight: 'bold',
  },

  iconImage: {
    width: 24,
    height: 24,
    margin: 10,
  },

  ImagenStyles: {
    width: 30,
    height: 30,
    margin: 10,
  },

  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingLeft: 5

  },
});
