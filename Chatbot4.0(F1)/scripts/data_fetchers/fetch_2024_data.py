import os
import time
import requests
import pandas as pd
import fastf1
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_exponential
import json
from functools import lru_cache

# Configure caching
CACHE_DIR = 'cache'
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

# API Configuration
OPENWEATHER_API_KEY = '07e9b69a901753d144df46077c7198f9'
ERGAST_API_BASE = "http://ergast.com/api/f1"
CIRCUIT_CACHE_FILE = 'circuit_coordinates.json'

# Configure retry policy
RACES_2024 = [
    (2024, 1), (2024, 2), (2024, 3), (2024, 4), (2024, 5),
    (2024, 6), (2024, 7), (2024, 8), (2024, 9), (2024, 10),
    (2024, 11), (2024, 12), (2024, 13), (2024, 14), (2024, 15),
    (2024, 16), (2024, 17), (2024, 18), (2024, 19), (2024, 20),
    (2024, 21), (2024, 22), (2024, 23)
]

# Load or create circuit coordinate cache
if os.path.exists(CIRCUIT_CACHE_FILE):
    with open(CIRCUIT_CACHE_FILE, 'r') as f:
        circuit_cache = json.load(f)
else:
    circuit_cache = {}

def save_circuit_cache():
    with open(CIRCUIT_CACHE_FILE, 'w') as f:
        json.dump(circuit_cache, f)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_weather(api_key, lat, lon, timestamp):
    """Fetch weather data with retry logic"""
    url = f"https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={lat}&lon={lon}&dt={timestamp}&appid={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Weather API error: {e}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_ergast_lap_data(year, round_number):
    """Fetch Ergast data with retry logic"""
    try:
        url = f"{ERGAST_API_BASE}/{year}/{round_number}/laps.json?limit=2000"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()['MRData']['RaceTable']['Races'][0]['Laps']
    except Exception as e:
        print(f"Ergast API error: {e}")
        raise

def get_circuit_coordinates(session):
    """Get coordinates with caching"""
    cache_key = f"{session.event['EventName']}_{session.date.year}"
    if cache_key in circuit_cache:
        return circuit_cache[cache_key]
    
    circuit_info = session.get_circuit_info()
    coords = (circuit_info.location["lat"], circuit_info.location["long"])
    circuit_cache[cache_key] = coords
    save_circuit_cache()
    return coords

def process_driver(session, driver, ergast_lap_data, start_time, end_time):
    """Process data for a single driver"""
    try:
        laps = session.laps.pick_driver(driver)
        driver_info = session.get_driver(driver)
        fastest_lap = laps.pick_fastest()
        
        # Get circuit coordinates from cache or API
        lat, lon = get_circuit_coordinates(session)
        
        # Fetch weather data
        weather_data = fetch_weather(OPENWEATHER_API_KEY, lat, lon, start_time)
        rain_status = any(hour.get('rain') for hour in weather_data.get('hourly', []) 
                        if start_time <= hour['dt'] <= end_time) if weather_data else False

        # Base data
        race_data = {
            'Race': session.event['EventName'],
            'Date': session.date,
            'Driver': driver_info['FullName'],
            'Team': driver_info['TeamName'],
            'Starting Position': driver_info['GridPosition'],
            'Finish Position': driver_info['Position'],
            'Fastest Lap Time': fastest_lap['LapTime'] if not fastest_lap.empty else pd.NaT,
            'Laps Completed': len(laps),
            'Overtakes': len(laps) - driver_info['GridPosition'],
            'DNF': 'Yes' if driver_info['Status'] != 'Finished' else 'No',
            'Tire Compounds': ', '.join(laps['Compound'].unique()),
            'Rain During Race': 'Yes' if rain_status else 'No'
        }

        # Add Ergast data if available
        if ergast_lap_data:
            driver_laps = [lap for lap in ergast_lap_data if lap['driverId'] == driver]
            race_data['Ergast Laps'] = len(driver_laps) if driver_laps else pd.NA

        return race_data

    except Exception as e:
        print(f"Error processing driver {driver}: {e}")
        return None

def process_race(year, round_number):
    """Process a single race with parallel driver processing"""
    try:
        session = fastf1.get_session(year, round_number, 'R')
        session.load()
        time.sleep(2)  # Reduced sleep between sessions

        # Get time window for weather
        start_time = int(session.date.timestamp())
        end_time = start_time + 7200  # 2-hour window

        # Fetch data in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            ergast_data = fetch_ergast_lap_data(year, round_number)
            
            for driver in session.drivers:
                futures.append(executor.submit(
                    process_driver, session, driver, ergast_data, start_time, end_time
                ))

            return [future.result() for future in futures if future.result() is not None]

    except Exception as e:
        print(f"Error processing race {year} R{round_number}: {e}")
        return []

def process_data(races):
    """Main processing function with parallel race processing"""
    all_data = []
    with ThreadPoolExecutor(max_workers=2) as executor:  # Process 2 races at once
        futures = {executor.submit(process_race, year, round): (year, round) 
                 for year, round in races}
        
        for future in futures:
            try:
                all_data.extend(future.result())
            except Exception as e:
                print(f"Error getting future result: {e}")

    return pd.DataFrame(all_data)

def save_to_excel(df, template_path):
    """Save data to Excel with error handling"""
    df.replace({pd.NaT: None}, inplace=True)
    try:
        with pd.ExcelWriter(template_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, index=False, sheet_name='2024 Race Data')
        print(f"Data saved successfully to {template_path}")
    except Exception as e:
        print(f"Excel save error: {e}")

if __name__ == "__main__":
    start_time = time.time()
    
    df = process_data(RACES_2024)
    print(f"Processing completed in {time.time() - start_time:.2f} seconds")
    
    print("\nMissing values summary:")
    print(df.isnull().sum())
    
    TEMPLATE_PATH = r'C:\Users\Joseph N Nimyel\OneDrive\Documents\Chatbot\Chatbot3.0(F1)\F1 Seasons.xlsx'
    save_to_excel(df, TEMPLATE_PATH)
    print("\nFirst 5 rows of data:")
    print(df.head())