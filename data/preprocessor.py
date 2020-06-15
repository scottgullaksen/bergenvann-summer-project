from data.raw_reader import CSVFileReader
import logging
import os

class Preprocessor(object):
	"""
	Wrapper for raw reader class. Preprocceses the files/datapoints, 
	and creates and places into organised file structure. This is a convinient
	place to place heavy time/memory consuming preprocessing functions to
	the data such as aggregation, frequency analysis, etc. 

	Args:
		reader (object): The reader object to be wrapped. Provides reading capabilities to the dataset 
	"""
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

	def transform(self, pickle_keys: list):

		# Go through each pump station file
		# Go through each row
		# determnine date of first row
		# Find the file for that date. If doesnt exist, create new
		# Keep adding datapoints to correct place in dict until new day

		for kwrd in pickle_keys:
			for idx, raw in enumerate(
				self.csv_reader.yield_rows(dir_or_filename= kwrd)
			):
				data = self.clean_pump_data(raw)

				if idx == 1: self.logger.info(f'raw row got cleaned to {data}')

if __name__ == "__main__":

	preprocessor = Preprocessor()

	preprocessor.clean_pump_data()