import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, time

def to_dataframes(day_iterator):
	"""
	Args:
		day_iterator: The generator/iterable returned from the reading functions from the reader module

	Returns:
		A dict of dataframes corresponding to each station where the dataframe
		holds the measurments for that station
	"""

	dict_result = {}

	# day is dict of stations with measures for that day
	for day in day_iterator:
		for station, data in day['hours'].items():  # Data is dict of measurments
			if station not in dict_result:
				# Initilize the station to result with first dict of measurments
				dict_result[station] = data
			else:
				for measurement in dict_result[station]:
					# Extend the measurement at the station with measurement of next day
					dict_result[station][measurement].extend(data[measurement])
	dict_of_df = {
		station: pd.DataFrame(meas) for station, meas in dict_result.items()
	}
	for df in dict_of_df.values():
		df.set_index('date', inplace= True)
		df.sort_index(inplace= True)
	return dict_of_df

def get_summer_weather_stats():
	df_dict = to_dataframes(reader.get_data(
		#date1= date1
		#date2= date2
		months=string_range(6, 7),
		#years=string_range(2012, 2018),
		#days= string_range(1, 2),
	))
	time = time(12, 0, 0)
	df = df_dict['vaerdata']

	df = df[ df['date'].apply(lambda d: d.time()) > time ]

	print(df)
	print(df.describe())



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

def plot(df: pd.DataFrame):
	df.plot()
	plt.show()


if __name__ == "__main__":
	from data.reader import PickledDataReader
	from util import *

	reader = PickledDataReader()
	
	date1 = datetime(2020, 6, 1)
	date2 = datetime(2015, 6, 25)

	df_dict = to_dataframes(reader.get_data(
		date1= date1
		#date2= date2
		#months=string_range(7, 8),
		#years=string_range(2012, 2018),
		#days= string_range(1, 2),
	))

	description = {  # of what plot will show
		'vaerdata': ['precipitation (mm)'],
		'ThorM߸hlensVilVite': ['quantity (l/s)']
	}

	df = merge_stations(df_dict, description)

	plot(df)