import logging
import logging.config
import yaml
import os
import pickle
import pandas as pd
from datetime import datetime, timedelta
from .util import abspath, find_first_filepath, find_last_filepath, keys


with open('./logging.yaml', 'r') as f:
	log_cfg = yaml.safe_load(f.read())

logging.config.dictConfig(log_cfg)

class PickledDataReader(object):
	"""
	Reader class that provides a convienent and fast API for accessing subsets
	of the preproccesd data points located in the file structure indicated
	by the variable "path". 
	"""
	def __init__(self, path= None):

		self.logger = logging.getLogger('dev')
		self.logger.setLevel(logging.INFO)

		# Path to processed file directory
		self.path = os.path.normpath(
			os.path.join(
				os.path.dirname(__file__), 'pickled_data'
			)
		)

	def __path_to_date(self, path) -> datetime:
		return datetime.strptime(
			os.path.splitext(os.path.relpath(path, self.path))[0], '%Y\\%m\\%d'
		)

	def __resolve_dates(self, date1: datetime, date2: datetime):
		"""
		Gives the provided dates a upper/minimum bound if not specified (is None)
		or doesnt exist
		"""
		if not date1 or not os.path.exists(abspath(self.path, date1)):
			path = find_first_filepath(self.path)
			self.logger.warning(f'Too early/no date specified ({date1}) - no path found. Using earliest file insted {path}')
			date1 = self.__path_to_date(path)

		if not date2 or not os.path.exists(abspath(self.path, date2)):
			path = find_last_filepath(self.path)
			self.logger.warning(f'Too late/no date specified ({date2}) - no path found. Using earliest file insted {path}')
			date2 =  self.__path_to_date(path)
		return date1, date2

	def __combine_path(self, path1, path2):
		"""
		Replaces the first part of path2 with path1
		"""
		p1_tail = os.path.relpath(path1, self.path)
		p2_tail = os.path.relpath(path2, self.path)

		p1_parts = os.path.normpath(p1_tail).split(os.path.sep)
		p2_parts = os.path.normpath(p2_tail).split(os.path.sep)
		p2_parts = p2_parts[len(p1_parts):] if len(p2_parts) > len(p1_parts) else []
		return os.path.join(self.path, *p1_parts, *p2_parts)

	def __get_paths_to_basenames(self, paths: list, basenames: list, date1: datetime, date2: datetime):
		"""
		Generates paths to basenames relative to paths between specified dates (if they exist).

		If basenames is None, generates paths to all subdirs under paths.

		If both dates is None, generates from all dates avalable.
		"""
		date1, date2 = self.__resolve_dates(date1, date2)

		path1 = abspath(self.path, date1)
		path2 = abspath(self.path, date2)

		for path in paths:
			for basename in os.listdir(path):
				# Construct new path to subdirs
				new_path = os.path.join(path, basename)

				# If basename not specified, yield all paths to subdirs
				# else yield the ones specified in basenames
				if not basenames or os.path.splitext(os.path.basename(new_path))[0] in basenames:
					# Only yield if new path is between date1 and date2
					if (date1 <= self.__path_to_date(self.__combine_path(new_path, path1))
					and
					date2 >= self.__path_to_date(self.__combine_path(new_path, path2))):
						yield new_path

	def __get_paths_between_dates(self, date1: datetime, date2: datetime):
		"""
		Returns paths to files with content belonging between the specified dates
		"""
		date1, date2 = self.__resolve_dates(date1, date2)
		return [
			abspath(self.path, date) for date in [
				(date2 - timedelta(x)) for x in range((date2 - date1).days + 1)
			]
		]

	def __as_dataframes(self, day_iterator):
		"""
		Args:
			day_iterator: The generator/iterable returned from get_data

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

	def get_earliest_date(self): return self.__path_to_date(find_first_filepath(self.path))

	def get_latest_date(self): return self.__path_to_date(find_last_filepath(self.path))

	def get_available_years(self): return os.listdir(self.path)

	def get_stations(self): return keys  # Should change so reads from pickled corpus instead

	def get_file_content(self, paths: list):
		for file_path in paths:
			with open(file_path, 'rb') as f:
				yield pickle.load(f)

	def get_data(self, date1: datetime= None, date2: datetime= None, years:list= None,
					months: list= None, days:list= None, weekdays: list= [], df= True):
		"""
		Generates all contentes af all files specified by the arguments:

		Args:
			date1, date2: Yields contents between these. Unspecified yields from first date available to last
			years, months, days: Specify a list of years, months and days you would 
				like to see content from between date1 and date2.
				Unspecified yields everything available from that time period
		
		Example:
			get_data(date1= date, years= ['2011]) yields all contents from date1 only in 2011
		"""
		if not any([years, months, days]):  # of these specified, just use date range to construct paths. Faster
			print('called')
			paths = self.__get_paths_between_dates(date1, date2)
		else:
			# Construct full paths
			paths = [self.path]
			for time_periods in [years, months, days]:
				paths = self.__get_paths_to_basenames(paths, time_periods, date1, date2)

		# Filter, based on weekdays specified
		if weekdays:
			paths = (
				path for path in paths
				if self.__path_to_date(path).isoweekday() in weekdays
			)

		content = self.get_file_content(paths)

		return self.__as_dataframes(content) if df else content


# For testing
if __name__ == "__main__":
	reader = PickledDataReader()

	date1 = datetime(2015, 1, 24)
	date2 = datetime(2015, 1, 24)

	for idx, data in enumerate(reader.get_data(date1, years= ['2016'], months=['01', '02'], weekdays=[7])):
		print(f'{idx} :')
		print(data)
		print(data['hours']['vaerdata']['date'][0].isoweekday())