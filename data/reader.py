import logging
import yaml

with open('./logging.yaml', 'r') as f:
	log_cfg = yaml.safe_load(f.read())

logging.config.dictConfig(log_cfg)

class PickledDataReader(object):
	import os
	"""
	Reader class that provides a convienent and fast API for accessing subsets
	of the preproccesd data points located in the file structure indicated
	by the variable "path". 
	"""
	def __init__(self, path= None):

		self.logger = logging.getLogger('dev')
		self.logger.setLevel(logging.INFO)

		# Path to processed file directory
		self.path = os.path.join(
			os.path.dirname(__file__), 'pickled_data'
		)

	def get_available_years(self): return os.listdir(self.path)

	def get_dirs_by_years(self, years: list= None):
		years = self.get_available_years() if not years else years
		for dirname in years:
			year_path = os.path.join(self.path, dirname)
			if os.path.exists(year_path):
				yield year_path
			else:
				self.logger.warning(f'the provided year {dirname} does not have a path')

	def get_dirs_by_months(self, years:list= None, months: list = None):
		year_paths = self.get_dirs_by_years(years)
		all_month_paths = [
			os.path.join(year_path, month)
			for year_path in year_paths for month in os.listdir(year_path)  # Flattens
		]
		if not months: return all_month_paths
		for month_path in all_month_paths:
			for month in months:
				if os.path.basename(month_path) == month:
					yield month_path
				else:
					self.logger.warning(f'the provided month {month} did not match any path')

	def get_dirs_to_months_between(self, date1: datetime, date2: datatime):
		pass

	def get_file_content(self, start_date, end_date):
		"""
		Retrieves and returns the content of the files specified
		by the date of their contents
		"""
		# Loop trhough all files
		#	if start date encountered, yield file content
		# 	break when end date passed
		pass

	def get_data(self, start_date, end_date, pump_time_step, weather_time_step):
		"""
		Return the the pump and weather data for each of the pump stations
		within the specified time period and time step
		"""
		for content in self.get_file_content(start_date, end_date):
			yield content[pump_time_step], content[weather_time_step]


if __name__ == "__main__":
	import os
	import pickle

	pickle_files = [
		os.path.join(root, name)
		for root, dir_, files in os.walk(os.path.join(os.path.dirname(__file__), 'pickled_data'))
		for name in files
	]

	idx = len(pickle_files) // 2

	with open(pickle_files[-100], 'rb') as f:
		print(pickle_files[-100])
		data = pickle.load(f)
		print(data['hours']['vaerdata'])