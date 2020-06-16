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

	def get_paths_by_basename(self, paths: list, basenames: list = None):
		"""
		Generator of all paths to basenames relative paths if they exist
		"""
		all_paths = (
			os.path.join(path, basename)
			for path in paths for basename in os.listdir(path)  # Flattens
		)
		if basenames is None: return all_paths
		return (
			path for path in all_paths
			if os.path.splitext(os.path.basename(path))[0] in basenames
		)
			

	def get_available_years(self): return os.listdir(self.path)

	def get_dirs_by_years(self, years: list= None):
		return self.get_paths_by_basename([self.path], years)

	def get_dirs_by_months(self, years:list= None, months: list = None):
		year_paths = self.get_dirs_by_years(years)
		return self.get_paths_by_basename(year_paths, months)

	def get_file_paths_by_ranges(self, years:list= None, months: list= None, days:list= None):
		month_paths = self.get_dirs_by_months(years, months)
		return self.get_paths_by_basename(month_paths, days)

	def get_file_content(self, paths: list):
		for file_path in paths:
			with open(file_path, 'rb') as f:
				yield pickle.load(f)

	def get_file_content_by_ranges(self, years:list= None, months: list= None, days:list= None):
		"""
		Returns a generator of file content belonging to the ranges of 
		years, months and days specified. If a parameter is not specified, the entire
		available range will be used.
		"""
		return self.get_file_content(self.get_file_paths_by_ranges(years, months, days))

	def get_data_by_year_range(self, first_year: str, last_year: str):
		"""
		Returns all file content belonging to the range of years specified.
		"""
		year_range = [str(year) for year in range(int(first_year), int(last_year) + 1)]
		return self.get_file_content_by_ranges(year_range)

	def get_data_by_month_range(self, first_month, second_month):
		"""
		Returns all file content from all years, but within the specified month range.
		"""
		month_range = [
			f'0{i}' if i < 10 else str(i)
			for i in range(int(first_month), int(second_month))
		]
		return self.get_file_content_by_ranges(months=month_range)

	def get_data_by_day_range(self, first_day, second_day):
		"""
		Returns all file content from all years and months,
		but within the specified day range.
		"""
		day_range = [
			f'0{i}' if i < 10 else str(i)
			for i in range(int(first_day), int(second_day))
		]
		return self.get_file_content_by_ranges(days=day_range)

	def get_data_between_dates(self, date1: datetime, date2: datetime):
		"""
		Returns data from files with content belonging between the specified dates
		"""
		if not os.path.exists(abspath(self.path, date1)):
			path = find_first_filepath(self.path)
			self.logger.warning(f'Too early date specified ({date1}) - no path found. Using earliest file insted {path}')
			date1 = path_to_date(self.path, path)

		if not os.path.exists(abspath(self.path, date2)):
			path = find_last_filepath(self.path)
			self.logger.warning(f'Too late date specified ({date2}) - no path found. Using earliest file insted {path}')
			date2 =  path_to_date(self.path, path)

		
		paths_between_dates = [
			abspath(self.path, date) for date in [
				(date2 - timedelta(x)) for x in range((date2 - date1).days + 1)
			]
		]

		return self.get_file_content(paths_between_dates)

if __name__ == "__main__":
	reader = PickledDataReader()

	print(f'available years: {reader.get_available_years()}')

	print(f'dirs to years {list(reader.get_dirs_by_years())}')

	month_paths = list(reader.get_dirs_by_months(years=['2010', '2018']))

	print(f'dirs to months {month_paths}')

	day_paths = list(reader.get_file_paths_by_ranges(years=['2010', '2018'], months= ['09'], days= ['12', '15']))

	print(f'dirs to days {day_paths}')

	date1 = datetime(2015, 1, 24)
	date2 = datetime(2015, 1, 25)

	for idx, data in enumerate(reader.get_data_between_dates(date1, date2)):
		print(f'{idx} :')
		print(data)