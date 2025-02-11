import os
import fastf1
import pandas as pd
import time

# Enable caching and ensure the cache directory exists
CACHE_DIR = r'C:\Users\Joseph N Nimyel\OneDrive\Documents\Chatbot\Chatbot3.0(F1)\cache\2020'
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

# Define all 2020 races (year, round number)
RACES_2020 = [
    (2020, 1),  # Austrian Grand Prix
    (2020, 2),  # Styrian Grand Prix
    (2020, 3),  # Hungarian Grand Prix
    (2020, 4),  # British Grand Prix
    (2020, 5),  # 70th Anniversary Grand Prix
    (2020, 6),  # Spanish Grand Prix
    (2020, 7),  # Belgian Grand Prix
    (2020, 8),  # Italian Grand Prix
    (2020, 9),  # Tuscan Grand Prix
    (2020, 10), # Russian Grand Prix
    (2020, 11), # Eifel Grand Prix
    (2020, 12), # Portuguese Grand Prix
    (2020, 13), # Emilia Romagna Grand Prix
    (2020, 14), # Turkish Grand Prix
    (2020, 15), # Bahrain Grand Prix
    (2020, 16), # Sakhir Grand Prix
    (2020, 17)  # Abu Dhabi Grand Prix
]

# Function to fetch sessions
def fetch_sessions(races):
    """Fetch and load race sessions."""
    sessions = []
    for year, round_number in races:
        try:
            session = fastf1.get_session(year, round_number, 'R')  # 'R' for Race
            session.load()
            sessions.append(session)
            time.sleep(5)  # Avoid overwhelming the API
        except Exception as e:
            print(f"Error loading session for {year} Round {round_number}: {e}")
    return sessions

# Function to process session data
def process_session_data(sessions):
    """Extract relevant data from sessions."""
    data = []
    for session in sessions:
        for driver in session.drivers:
            try:
                laps = session.laps.pick_driver(driver)
                driver_info = session.get_driver(driver)
                fastest_lap = laps.pick_fastest()

                data.append({
                    'Race': session.event['EventName'],
                    'Date': session.date,
                    'Driver': driver_info['FullName'],
                    'Team': driver_info['TeamName'],
                    'Starting Position': driver_info['GridPosition'],
                    'Finish Position': driver_info['Position'],
                    'Fastest Lap Time': fastest_lap['LapTime'] if not fastest_lap.empty else None,
                    'Number of Overtakes': len(laps) - driver_info['GridPosition'],
                    'DNF Status': 'Yes' if driver_info['Status'] != 'Finished' else 'No',
                    'Points Earned': driver_info['Points'],
                    'Tire Compounds Used': ', '.join(laps['Compound'].unique())
                })
            except Exception as e:
                print(f"Error processing data for driver {driver}: {e}")
    return pd.DataFrame(data)

# Save data to Excel
def save_to_excel(df, template_path, sheet_name='2020 Race Data'):
    """Save DataFrame to an Excel file."""
    with pd.ExcelWriter(template_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

# Main execution
if __name__ == "__main__":
    # Fetch sessions for 2020
    sessions_2020 = fetch_sessions(RACES_2020)

    # Process data
    df_2020 = process_session_data(sessions_2020)

    # Save data to Excel for visualization and cleaning
    TEMPLATE_PATH = r'C:\Users\Joseph N Nimyel\OneDrive\Documents\Chatbot\Chatbot3.0(F1)\F1 Seasons.xlsx'
    try:
        save_to_excel(df_2020, TEMPLATE_PATH)
        print(f"2020 data successfully saved to {TEMPLATE_PATH} in the sheet '2020 Race Data'.")
    except Exception as e:
        print(f"Error saving to Excel: {e}")