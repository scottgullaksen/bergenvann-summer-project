from data.raw_reader import CSVFileReader
import logging
import os

class Preprocessor(object):
	def __init__(self, csv_reader= None, target_dir= None):

		self.logger = logging.getLogger('dev')
		self.logger.setLevel(logging.INFO)

		self.csv_reader = CSVFileReader() if not csv_reader else csv_reader

		self.target = os.path.join(
			os.path.dirname(os.path.abspath(__file__)), 'data'
		) if not target_dir else target_dir

		# Make the target directory if it doesn't already exist
		if not os.path.exists(self.target):
			os.makedirs(self.target)


	def abspath(self, date):
		# Return a path to pickle file based on date provided
		# Create one if it doesnt exist
		pass

	def clean_pump_data(self, raw_data):
		"""
		Filters rows that contain actual data and cleans them
		"""

		first_char = raw_data[0][0] # should be numeral
		if len(raw_data) == 0 or not first_char.isnumeric():
			return None  # Irrelevant row

		date = raw_data[0]  # Date object

		quantity = raw_data[2]  # Float

		level = raw_data[4] # Foat



		

	def transform(self):

		# Go through each pump station file
		# Go through each row
		# determnine date of first row
		# Find the file for that date. If doesnt exist, create new
		# Keep adding datapoints to correct place in dict until new day

		for idx, raw in enumerate(
			self.csv_reader.yield_rows(dir_or_filename= 'pumpedata')
		):
			data = self.clean_pump_data(raw)

