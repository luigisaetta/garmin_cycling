#
# Utilities for parsing fit files and doing conversions
# Author: Luigi Saetta
#
from fitparse import FitFile
import pandas as pd
import numpy as np

DEBUG = False
#
# conversion functions
#
def convert_to_kmh(speed_list):
    kmh_speed_list = []

    for speed in speed_list:
        # converts from m/s
        speed = round(speed * 3.6, 2)
        kmh_speed_list.append(speed)

    return kmh_speed_list

# semicircles is a format used by Garmin in fit files
def semicircles_to_degrees(semicircles):
    try:
        # TODO check this round (to 7 after checking with wko data)
        deg = round(semicircles * (180.0 / 2**31), 7)
    except Exception as e:
        deg = None

    return deg

# from gpt4
# plus (LS) adjustment to handle NaN values
#
def compute_normalized_power(power_data):
    # Raise each power value to the fourth power
    fourth_power = np.power(power_data, 4)

    # Calculate a rolling 30-second average (assuming data is recorded every 1 second)
    # Adjust the window size if your data is recorded at a different frequency
    # (LS) It is ok, checked ts
    # (LS) modified to hanfle nan
    rolling_avg = pd.Series(fourth_power).rolling(window=30, min_periods=1, center=True).mean()

    # Take the fourth root of the average of these values
    normalized_power = np.power(rolling_avg, 1/4)
    
    return np.round(normalized_power, 1)

#
# read a fit file and store main infos in a Pandas DataFrame
#
def load_in_pandas(f_path_name):
    fitfile = FitFile(f_path_name)

    # the lists used to build the dataframe
    rec_num_list = []
    # timestamp
    ts_list = []
    lat_list = []
    long_list = []
    altitude_list = []
    speed_list = []
    power_list = []
    n_power_list = []
    cadence_list = []
    heart_rate_list = []
    temp_list = []

    # loop over all the records
    for i, record in enumerate(fitfile.get_messages('record')):
    
        rec_num_list.append(i+1)

        if DEBUG:
            if i < 10:
                print(f"Record num. {i}...")

        # extract record data
        for data in record:
            if DEBUG:
                if i < 10:
                    print(f"--- {data.name}, {data.value}")
        
            if data.name == "timestamp":
                ts_list.append(data.value)
            if data.name == "position_lat":
                lat_list.append(semicircles_to_degrees(data.value))
            if data.name == "position_long":
                long_list.append(semicircles_to_degrees(data.value))
            if data.name == "altitude":
                altitude_list.append(data.value)
            if data.name == "speed":
                speed_list.append(data.value)
            if data.name == "cadence":
                cadence_list.append(data.value)
            if data.name == "power":
                power_list.append(data.value)
            if data.name == "heart_rate":
                heart_rate_list.append(data.value)
            if data.name == "temperature":
                temp_list.append(data.value)
 
    #
    # prepare the dataframe
    #

    # conversion
    speed_list = convert_to_kmh(speed_list)
    n_power_list = compute_normalized_power(power_list)

    dict_values = {
        "id": rec_num_list,
        "timestamp": ts_list,
        "lat": lat_list,
        "long": long_list,
        "altitude": altitude_list,
        "temperature": temp_list,
        "speed": speed_list,
        "cadence": cadence_list,
        "power": power_list,
        "n_power": n_power_list,
        "heart_rate": heart_rate_list,
    }

    df = pd.DataFrame(dict_values)

    return df


