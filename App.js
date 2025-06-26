import 'react-native-gesture-handler';
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createDrawerNavigator, DrawerContentScrollView } from '@react-navigation/drawer';
import MainScreen from './components/MainScreen';
import Listado from './components/Listado';
<<<<<<< HEAD
import Calendario from './components/Calendario';
import AddAnimal from './components/AddAnimal';
import NewTask from './components/NewTask';
import { Text, TouchableOpacity, StyleSheet, View } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

const Drawer = createDrawerNavigator();

// Menú personalizado
function MenuLateral(props) {
  return (
    <DrawerContentScrollView {...props} contentContainerStyle={styles.drawer}>
      <DrawerItem
        label="Inicio"
        icon="home-outline"
        onPress={() => props.navigation.navigate('Inicio')}
      />
      <Text style={styles.sectionTitle}>Gestión de ganado</Text>
      <DrawerItem
        label="Listado"
        icon="clipboard-list-outline"
        onPress={() => props.navigation.navigate('Listado')}
      />
      <DrawerItem
        label="Agregar animal"
        icon="plus-box-outline"
        onPress={() => props.navigation.navigate('AddAnimal')}
      />
      <Text style={styles.sectionTitle}>Agenda</Text>
      <DrawerItem
        label="Calendario"
        icon="calendar-month-outline"
        onPress={() => props.navigation.navigate('Calendario')}
      />
      <DrawerItem
        label="Agregar tarea"
        icon="plus-box-outline"
        onPress={() => props.navigation.navigate('NewTask')}
      />
    </DrawerContentScrollView>
  );
}

function DrawerItem({ label, icon, onPress }) {
  return (
    <TouchableOpacity style={styles.item} onPress={onPress}>
      <Icon name={icon} size={24} color="#000" style={{ marginRight: 10 }} />
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
=======
import NewTask from './components/NewTask';
import AddAnimal from './components/AddAnimal';

export default function App() {
  return <AddAnimal />;
>>>>>>> main
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
    fontSize: 16,
    color: '#000',
  },
  sectionTitle: {
    fontWeight: 'bold',
    marginTop: 20,
    marginBottom: 8,
    marginLeft: 20,
    color: '#000',
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
});
