#
# Utilities for parsing fit files and doing conversions
# Author: Luigi Saetta
#

# for fit format
from fitparse import FitFile

# for TCX format
import xml.etree.ElementTree as ET

import pandas as pd
import numpy as np
import math

import matplotlib.pyplot as plt


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
    rolling_avg = (
        pd.Series(fourth_power).rolling(window=30, min_periods=1, center=True).mean()
    )

    # Take the fourth root of the average of these values
    normalized_power = np.power(rolling_avg, 1 / 4)

    return np.round(normalized_power, 1)


def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in meters
    r = 6371 * 1000

    # result in meters
    return c * r


def compute_total_distance(df):
    if df["distance"].max() is not np.nan:
        tot_dist = df["distance"].max()
    else:
        # else compute from lat, long
        tot_dist = 0

        lat_vet = df["position_lat"].values
        long_vet = df["position_long"].values

        for i in range(1, len(lat_vet)):
            p1_lat = lat_vet[i - 1]
            p1_long = long_vet[i - 1]
            p2_lat = lat_vet[i]
            p2_long = long_vet[i]

            dist = haversine(p1_lat, p1_long, p2_lat, p2_long)
            tot_dist += dist

    return round(tot_dist, 3)


def compute_energy_consumed(df, col_name, eff_factor=0.25):
    # we're assuming time between points is 1 sec.
    tot_energy_joule = np.sum(df[col_name].values)

    tot_energy_cal = tot_energy_joule * 0.000239006 * (1.0 / eff_factor)

    return round(tot_energy_cal, 1)


def print_debug_dict(dict_values):
    print("")
    print("Num. of elements in lists...")
    for key in dict_values.keys():
        print(key, len(dict_values[key]))
    
#
# read a fit file and store main infos in a Pandas DataFrame
#
def load_df_from_fit(f_path_name, cadence=False, power=False, debug=False):
    # power and cadence added to enable loading of data when power and cadence are NOT
    # available

    # read the binary file
    fitfile = FitFile(f_path_name)

    # the lists used to build the Pandas dataframe

    # list of data.name to consider
    # some id, n_power) are added..
    cols_list = [
        "id",
        "timestamp",
        "position_lat",
        "position_long",
        "altitude",
        "temperature",
        "speed",
        "distance",
        "heart_rate",
    ]

    # add cadence and power if available in the measurements
    if cadence:
        cols_list.append("cadence")
    if power:
        cols_list.append("power")
        cols_list.append("n_power")

    # initialize the dictionary
    dict_values = {}

    for key in cols_list:
        dict_values[key] = []

    # loop over all the records
    for i, record in enumerate(fitfile.get_messages("record")):
        if debug:
            # only 3 records displayed
            if i < 3:
                print(f"Record num. {i}...")

        # extract record data

        # to complete for the dataframe creation, to handle missing columns
        found_cols = []

        for data in record:
            if debug:
                if i < 3:
                    print(f"--- {data.name}, {data.value}")

            # more elegant
            if data.name in dict_values.keys():
                value = data.value
                found_cols.append(data.name)

                if data.name in ["position_lat", "position_long"]:
                    # conversion
                    value = semicircles_to_degrees(value)

                dict_values[data.name].append(value)

        # handle missing cols
        missing_cols = list(set(cols_list) - set(found_cols))

        for col in missing_cols:
            dict_values[col].append(np.nan)

    # now i + 2 is the # of records
    dict_values["id"] = range(1, i + 2)

    #
    # prepare the dataframe
    #

    # conversion
    dict_values["speed"] = convert_to_kmh(dict_values["speed"])

    # compute n_power
    if power:
        dict_values["n_power"] = compute_normalized_power(dict_values["power"])

    if debug:
        print_debug_dict(dict_values)

    df = pd.DataFrame(dict_values)

    return df


#
# Load TCX file
#
def load_df_from_tcx(f_pathname, cadence=False, power=False, debug=False):
    # Parse the XML file
    NAMESPACE = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
    XPATH_PREFIX = ".//" + "{" + NAMESPACE + "}"

    namespaces = {
        "ns3": "http://www.garmin.com/xmlschemas/ActivityExtension/v2"  # The namespace for ns3
    }

    tree = ET.parse(f_pathname)
    root = tree.getroot()

    cols_list = [
        "id",
        "timestamp",
        "position_lat",
        "position_long",
        "altitude",
        "distance",
        "speed",
        "heart_rate",
    ]

    # add cadence and power if available in the measurements
    if cadence:
        cols_list.append("cadence")
    if power:
        cols_list.append("power")
        cols_list.append("n_power")

    # initialize the dictionary
    dict_values = {}

    for key in cols_list:
        dict_values[key] = []

    i = 0
    for trackpoint in root.findall(XPATH_PREFIX + "Trackpoint"):
        # Extract data from each trackpoint

        try:
            time = trackpoint.find(XPATH_PREFIX + "Time")

            position = trackpoint.find(XPATH_PREFIX + "Position")
            latitude = position.find(XPATH_PREFIX + "LatitudeDegrees")
            longitude = position.find(XPATH_PREFIX + "LongitudeDegrees")

            altitude = trackpoint.find(XPATH_PREFIX + "AltitudeMeters")
            distance = trackpoint.find(XPATH_PREFIX + "DistanceMeters")
            heart_rate = trackpoint.find(XPATH_PREFIX + "Value")

            # extensions
            speed = trackpoint.find(".//ns3:Speed", namespaces)

            dict_values["timestamp"].append(time.text)
            dict_values["position_lat"].append(latitude.text)
            dict_values["position_long"].append(longitude.text)
            dict_values["altitude"].append(float(altitude.text))
            dict_values["distance"].append(float(distance.text))
            dict_values["heart_rate"].append(float(heart_rate.text))
            dict_values["speed"].append(float(speed.text))

            i += 1

            if debug:
                if i < 3:
                    print(time.text)
                    print(latitude.text)

        except Exception as e:
            # for any exception it skips the point
            print(f"Exception: time: {time.text}, {str(e)}")

    # now i + 1 is the # of records
    dict_values["id"] = range(1, i + 1)

    # conversion
    dict_values["speed"] = convert_to_kmh(dict_values["speed"])

    if debug:
        print_debug_dict(dict_values)

    df = pd.DataFrame(dict_values)

    return df


# for plotting
def plot_vs_altitude(df, col_name, smooth=False):
    # if smooth make a 60 sec. window rolling avg

    y = df[col_name].values
    if smooth:
        rolling_avg = df[col_name].rolling(window=60, min_periods=1, center=True).mean()
        y = rolling_avg

    plt.plot(df["id"].values, y, label=col_name)
    plt.plot(df["id"].values, df["altitude"].values, label="altitude")
    plt.title(col_name + " vs altitude")
    plt.xlabel("point #")
    plt.legend()
    plt.grid(True)
    plt.show()
