import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function Calendario({ navigation }) {
  return (
    <View style = {styles.month}>
              <View style = {styles.MonthNameContainer}>
                <Text style = {styles.monthText}>
                  {MonthName.charAt(0).toUpperCase() + MonthName.slice(1)} {year}
                </Text>
              </View>
    
              <View style = {styles.WeekDayTextContainer}>
                <Text style = {styles.dayText}>
                  L
                </Text>
                <Text style = {styles.dayText}>
                  M
                </Text>
                <Text style = {styles.dayText}>
                  M
                </Text>
                <Text style = {styles.dayText}>
                  J
                </Text>
                <Text style = {styles.dayText}>
                  V
                </Text>
                <Text style = {styles.dayText}>
                  S
                </Text>
                <Text style = {styles.dayText}>
                  D
                </Text>
              </View>
              
              {/* Days of the month */}
              <View style = {styles.dayTextContainer}>
                {getWeekDates().map((day, index) => (
                  <Text key={index} style={[styles.dayText,day === date.getDate() && styles.currentDate]}>
                     {day}
                  </Text>
                ))}
              </View>
            </View>
  );
}
const styles = StyleSheet.create({
  month: {
    flex: 1,
    backgroundColor: '#fffbfa',
    padding:5,
    borderRadius: 25,
    gap: 15
  },

  MonthNameContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignContent: 'center',
  },

  WeekDayTextContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },

  dayTextContainer: { 
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 1,
  },
  currentDate:{
    backgroundColor: '#B8F574',
    borderRadius: 100,
    padding: 5,
    paddingVertical:1,
  }
});


let date = new Date();
let year = date.getFullYear();
let MonthName = date.toLocaleString('es-ES', { month: 'long'});
function getWeekDates(){
  let daysWeek = date.getDay();
  let newDate = new Date(date);
  const diffToMonday = daysWeek === 0 ? -6 : 1 - daysWeek;
  newDate.setDate(date.getDate() + diffToMonday);

  const weekDates = [];
  for (let i = 0; i < 7; i++) {
    const day = new Date(newDate);
    day.setDate(newDate.getDate() + i);
    weekDates.push(day.getDate());
  }
  return weekDates;
}

