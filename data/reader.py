import logging
import logging.config
import yaml
import os
import pickle
from datetime import datetime, timedelta
from util import abspath, find_first_filepath, find_last_filepath, path_to_date

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

	def get_available_years(self): return os.listdir(self.path)

	def __resolve_dates(self, date1: datetime, date2: datetime):
		if not date1 or not os.path.exists(abspath(self.path, date1)):
			path = find_first_filepath(self.path)
			self.logger.warning(f'Too early/no date specified ({date1}) - no path found. Using earliest file insted {path}')
			date1 = path_to_date(self.path, path)

		if not date2 or not os.path.exists(abspath(self.path, date2)):
			path = find_last_filepath(self.path)
			self.logger.warning(f'Too late/no date specified ({date2}) - no path found. Using earliest file insted {path}')
			date2 =  path_to_date(self.path, path)
		return date1, date2

	def __combine_path(self, path1, path2):
		p1_tail = os.path.relpath(path1, self.path)
		p2_tail = os.path.relpath(path2, self.path)

		p1_parts = os.path.normpath(p1_tail).split(os.path.sep)
		p2_parts = os.path.normpath(p2_tail).split(os.path.sep)
		p2_parts = p2_parts[len(p1_parts):] if len(p2_parts) > len(p1_parts) else []
		return os.path.join(self.path, *p1_parts, *p2_parts)


	def __get_paths_by_basename(self, paths: list, basenames: list, date1: datetime, date2: datetime):
		"""
		Generates paths to basenames relative to paths between specified dates.

		If basenames is None, generates paths to all subdirs under paths.

		If both dates is None, generates from all time periods.
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
					if all([  # Check if new path lies between dates before yielding
						date1 <= path_to_date(
							self.path,
							self.__combine_path(new_path, path1)
						),
						date2 >= path_to_date(
							self.path,
							self.__combine_path(new_path, path2)
						)
					]):
						yield new_path

	def get_file_content(self, paths: list):
		for file_path in paths:
			with open(file_path, 'rb') as f:
				yield pickle.load(f)

	def get_data(self, date1: datetime= None, date2: datetime= None, years:list= None, months: list= None, days:list= None):
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

		# Find all relevant paths
		paths = [self.path]
		for time_periods in [years, months, days]:
			paths = self.__get_paths_by_basename(paths, time_periods, date1, date2)

		return self.get_file_content(paths)


if __name__ == "__main__":
	reader = PickledDataReader()

	print(f'available years: {reader.get_available_years()}')

	date1 = datetime(2015, 1, 24)
	date2 = datetime(2015, 1, 24)

	for idx, data in enumerate(reader.get_data(date1, years= ['2016'], days= ['07', '08'])):
		print(f'{idx} :')
		print(data)