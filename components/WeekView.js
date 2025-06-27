import React from 'react';
import { Platform } from 'react-native';
import { View, Text, StyleSheet } from 'react-native';

export default function WeekView() {
  const today = new Date();
  const startOfWeek = new Date(today);
  startOfWeek.setDate(today.getDate() - (today.getDay() === 0 ? 6 : today.getDay() - 1)); // lunes

  const weekDays = [...Array(7)].map((_, index) => {
    const date = new Date(startOfWeek);
    date.setDate(date.getDate() + index);
    const isToday = date.toDateString() === today.toDateString();
    return (
      <View key={index} style={[styles.dayContainer, isToday && styles.today]}>
        <Text style={[styles.dayLabel, isToday && styles.todayText]}>
          {['L', 'M', 'M', 'J', 'V', 'S', 'D'][index]}
        </Text>
        <Text style={[styles.dateLabel, isToday && styles.todayText]}>
          {date.getDate()}
        </Text>
      </View>
    );
  });

  return <View style={styles.container}>{weekDays}</View>;
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#fff',
    paddingVertical: 5,
  },
  dayContainer: {
    alignItems: 'center',
    padding: 6,
  },
  dayLabel: {
    fontSize: 14,
    color: '#555',
    fontFamily: Platform.OS === 'ios' ? 'System' : 'sans-serif',
  },
  dateLabel: {
    fontSize: 16,
    color: '#000',
    fontFamily: Platform.OS === 'ios' ? 'System' : 'sans-serif',
  },
  today: {
    borderBottomWidth: 2,
    borderBottomColor: '#B8F574',
  },
  todayText: {
    color: '#000',
    fontWeight: 'bold',
  },
});
