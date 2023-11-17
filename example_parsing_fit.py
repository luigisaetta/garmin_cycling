#
# Test parse fit format files (Garmin)
#
import sys
from fitparse import FitFile
import pandas as pd
import numpy as np

from utility import semicircles_to_degrees, convert_to_kmh, compute_normalized_power, load_in_pandas

DEBUG = True


#
# Main
#

# read the file name from the command line
if len(sys.argv) < 2:
    print("Usage: python example.py file_name")
    sys.exit(1)  # Exit the script with an error code

FILE_NAME = sys.argv[1]

df = load_in_pandas(FILE_NAME)

# print the head of dataframe
print(df.head(10))

# compute some stats
avg_hr = np.mean(df['heart_rate'].values)
avg_speed = np.mean(df['speed'].values)
avg_pwr = np.mean(df['power'].values)
avg_np_pwr = np.mean(df['n_power'].values)
min_alt = np.min(df['altitude'].values)
max_alt = np.max(df['altitude'].values)

print()
print("Statistics:")
print(f"Avg HR: {avg_hr:.0f}")
print(f"Avg speed: {avg_speed:.1f} kmh")
print(f"Altitude: min={min_alt:.1f}, max={max_alt:.1f}")
print(f"Avg power: {avg_pwr:.1f} watt")
print(f"Avg normalized power: {avg_np_pwr:.1f} watt")

# save the file to csv
new_file_name = FILE_NAME.split(".")[0] + ".csv"
df.to_csv(new_file_name, index=None)



