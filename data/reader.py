class PickledDataReader(object):
	import os
	"""
	Reader class that provides a convienent and fast API for accessing subsets
	of the preproccesd data points located in the file structure indicated
	by the variable "path". 
	"""
	def __init__(self, path= None):

		# Path to processed file directory
		self.path = os.path.join(__file__, "preprocessed_data") if not path else path

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