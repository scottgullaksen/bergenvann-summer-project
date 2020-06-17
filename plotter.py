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
					dict_result[station][measurement].extend(data[measurement])

	return { station: pd.DataFrame(meas) for station, meas in dict_result.items() }