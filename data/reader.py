class PickledDataReader(object):
	import os
	"""
	Reader class that provides a convienent and fast API for accessing subsets
	of the preproccesd data points located in the file structure indicated
	by the variable "path". 
	"""
	def __init__(self, path= None):

		# Path to processed file directory
		self.path = os.path.join(
			os.path.dirname(__file__), 'pickled_data'
		)

	def get_available_years(self): return os.listdir(self.path)

	def get_dirs_by_years(self, years: list= None):
		years = self.get_available_years() if not years else years
		if not set(years).issubset(set(self.get_available_years())):
			raise ValueError('some of the years specified does not have a path')
		return [ os.path.join(self.path, dirname) for dirname in years ]
		
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