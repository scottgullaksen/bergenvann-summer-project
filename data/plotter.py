import pandas as pd
import matplotlib.pyplot as plt

def to_dataframes(day_iterator):
	"""
	Args:
		day_iterator:
			The generator/iterable returned from the reading functions
			from the reader module
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

	return { station: pd.DataFrame(meas) for station, meas in dict_result.items() }


if __name__ == "__main__":
	from reader import PickledDataReader
	from datetime import datetime, time
	from util import *

	reader = PickledDataReader()
	
	date1 = datetime(2015, 1, 24)
	date2 = datetime(2015, 1, 25)

	df_dict = to_dataframes(reader.get_data(
		#date1= date1
		#date2= date2
		months=string_range(7, 7),
		#years=string_range(2012, 2018),
		#days= string_range(1, 31),
	))
	time = time(12, 0, 0)
	df = df_dict['vaerdata']

	df = df[ df['date'].apply(lambda d: d.time()) > time ]

	# Get statistics about summer day weather
	print(df.describe())

	for station, df in df_dict.items():

		print(station)
		df.info()