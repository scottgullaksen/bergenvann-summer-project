from datetime import datetime, timedelta
import pandas as pd
import os
import numpy as np

PUMPSTATIONS = [
    os.path.splitext(filename)[0]
    for filename in os.listdir(
        os.path.normpath(
            os.path.join(os.path.dirname(__file__), 'raw_data/pumpedata') 
        )
    ) if os.path.splitext(filename)[1] == '.csv'
]

def abspath(path, date: datetime):
    """
    Returns the absolute target file path for the specified date 
    relative to the provided path
    """
    return os.path.normpath(
        os.path.join(path, date.strftime('%Y/%m/%d') + '.pickle')
    )

def find_first_filepath(path: os.path) -> os.path:
    for dirpath, dirname, filenames in os.walk(path):
        for filename in filenames:
            return os.path.join(dirpath, filename)

def find_last_filepath(path: os.path) -> os.path:
    if os.path.isfile(path):
        return path
    return find_last_filepath(
        os.path.join(
            path,
            max(os.listdir(path), key= lambda c: int(c) if c.isnumeric() else int(
                os.path.splitext(c)[0]
            ))
        )
    )

# NOT IN USE
def string_range(first: int, last: int):
    """Create a string representation of the range"""
    return [
        f'0{i}' if i < 10 else str(i) for i in range(first, last + 1)
    ]

# ONLY USED IN MODELING SCRPITS, SHOULD SWITCH TO stream_to_dataframe
def merge_stations(result: dict, stations: dict, left_df: pd.DataFrame= None):
    """
    Merge all stations values

    Args:
        result: dict of pandas dataframes
        stations: dict of stations (str) (keys) to be included in plot and
        a list of the stations measurments(values) to be shown as
    """
    if left_df is None:  # First stack call
        stations = {  # Filter away stations not in result
            s:v for s,v in stations.items() if s in result
        }
    if not stations: return left_df  # Base case
    right_key = list(stations.keys())[0]
    right_df = result[right_key][stations.pop(right_key)]
    return merge_stations(
        result= result,
        left_df= pd.merge(left_df, right_df, how='outer', right_index= True, left_index= True)
        if left_df is not None else right_df,
        stations= stations
    )

def stream_to_dataframe(datapoints, stations):
    
    # Determine column names
    all_meas = [m for meas in stations.values() for m in meas]
    col_name = {
        (m, s): (f'{m} ({s})' if all_meas.count(m) > 1 else m)
          for s, meas in stations.items() for m in meas
    }
    
    def extract_data(d):
        extracted = {
            col_name[(m, s)]: d[s][m] for s, meas in stations.items()
               for m in meas if s in d and m in d[s]
        }
        extracted['date'] = d['date']
        return extracted
    
    df = pd.DataFrame([
        extract_data(d) for d in datapoints
        if any(s in d for s in stations)
    ])
    
    if not df.empty:
        df.set_index('date', inplace= True)
        #df.sort_index(inplace= True)

    return df