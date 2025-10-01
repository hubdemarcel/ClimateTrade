#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/climatetrade.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM weather_data')
total = cursor.fetchone()[0]
print(f'Total weather records: {total}')

# Check source_id values in weather_data
cursor.execute('SELECT DISTINCT source_id FROM weather_data LIMIT 5')
source_ids = cursor.fetchall()
print('Source IDs in weather_data:', [row[0] for row in source_ids])

# Check source IDs in weather_sources
cursor.execute('SELECT id, source_name FROM weather_sources')
source_mapping = dict(cursor.fetchall())
print('Source ID mapping:', source_mapping)

# Check the actual data types
cursor.execute('SELECT source_id, typeof(source_id) FROM weather_data LIMIT 3')
data_types = cursor.fetchall()
print('Data types in weather_data:', data_types)

# Try the JOIN again
cursor.execute('SELECT ws.source_name, COUNT(*) FROM weather_data wd JOIN weather_sources ws ON wd.source_id = ws.id GROUP BY ws.source_name ORDER BY COUNT(*) DESC')
print('Records by source:')
results = cursor.fetchall()
if results:
    for row in results:
        print(f'  {row[0]}: {row[1]} records')
else:
    print('  No data found - checking raw data')
    cursor.execute('SELECT source_id, COUNT(*) FROM weather_data GROUP BY source_id')
    raw_results = cursor.fetchall()
    for row in raw_results:
        source_name = source_mapping.get(row[0], f'Unknown({row[0]})')
        print(f'  {source_name}: {row[1]} records')

# Also check sources table
cursor.execute('SELECT source_name, active FROM weather_sources ORDER BY source_name')
print('\nWeather sources:')
for row in cursor.fetchall():
    status = 'Active' if row[1] else 'Inactive'
    print(f'  {row[0]}: {status}')

# Show some actual temperature data
print('\nSample temperature data:')
cursor.execute('''
    SELECT wd.location_name, ws.source_name, wd.temperature, wd.timestamp
    FROM weather_data wd
    JOIN weather_sources ws ON wd.source_id = ws.id
    ORDER BY wd.timestamp DESC
    LIMIT 10
''')
sample_data = cursor.fetchall()
for row in sample_data:
    print(f'  {row[0]} ({row[1]}): {row[2]}°F at {row[3]}')

# Show temperature ranges
print('\nTemperature ranges by location:')
cursor.execute('''
    SELECT wd.location_name,
           MIN(wd.temperature) as min_temp,
           MAX(wd.temperature) as max_temp,
           AVG(wd.temperature) as avg_temp,
           COUNT(*) as count
    FROM weather_data wd
    GROUP BY wd.location_name
    ORDER BY wd.location_name
''')
temp_ranges = cursor.fetchall()
for row in temp_ranges:
    print(f'  {row[0]}: {row[1]:.1f}°F - {row[2]:.1f}°F (avg: {row[3]:.1f}°F, {row[4]} records)')

conn.close()