#
# Oracle 2023
# Author: L.S.
#
import xml.etree.ElementTree as ET
from glob import glob
import numpy as np
import time


NAMESPACE = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
XPATH_PREFIX = ".//" + "{" + NAMESPACE + "}"

hr_list = []


def read_tcx(file_path):
    # Parse the XML file
    namespaces = {
        "ns3": "http://www.garmin.com/xmlschemas/ActivityExtension/v2"  # The namespace for ns3
    }

    tree = ET.parse(file_path)
    root = tree.getroot()

    # Iterate through the elements you are interested in
    # For example, to get trackpoints:
    for trackpoint in root.findall(XPATH_PREFIX + "Trackpoint"):
        # Extract data from each trackpoint

        try:
            time = trackpoint.find(XPATH_PREFIX + "Time")
            position = trackpoint.find(XPATH_PREFIX + "Position")
            latitude = position.find(XPATH_PREFIX + "LatitudeDegrees")
            longitude = position.find(XPATH_PREFIX + "LongitudeDegrees")
            altitude = trackpoint.find(XPATH_PREFIX + "AltitudeMeters")
            heart_rate = trackpoint.find(XPATH_PREFIX + "Value")

            # extensions
            speed = trackpoint.find(".//ns3:Speed", namespaces)

            # Print or process the data
            print(f"Time: {time.text if time is not None else 'N/A'}")
            print(f"Latitude: {latitude.text if latitude is not None else 'N/A'}")
            print(f"Longitude: {longitude.text if longitude is not None else 'N/A'}")
            print(f"Altitude: {altitude.text if altitude is not None else 'N/A'}")
            print(f"Heart Rate: {heart_rate.text if heart_rate is not None else 'N/A'}")

            # extensions
            print(f"Speed: {float(speed.text):.2f}")

            print("-----")
            print("")

            hr_list.append(float(heart_rate.text))
        except Exception as e:
            print("Anomaly found...")

    n_trackpoint = len(hr_list)
    hr_avg = np.mean(hr_list)

    # stats
    print("")
    print(f"Num. of trackpoint is: {n_trackpoint}")
    print(f"Avg HR is: {hr_avg:.0f}")
    print("")


# Usage
file_list = glob("*.tcx")

for f_name in file_list:
    print("")
    print(f"---- processing {f_name}...")
    print("--------------------------")
    print("--------------------------")

    read_tcx(f_name)
    print("")
