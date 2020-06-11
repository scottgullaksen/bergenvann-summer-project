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

	def get_data(self, start_date, end_date, pump_time_step, weather_time_step):
		"""
		Retrieves data for each of the pump stations and weather 
		within the specified time frame and time steps
		"""
		pass