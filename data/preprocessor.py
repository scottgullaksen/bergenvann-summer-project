from data.raw_reader import CSVFileReader
import logging
import os
from datetime import datetime
import pickle

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


	def abspath(self, date: datetime):
		"""
		Returns the absolute target file path for the specified date
		"""
		return os.path.normpath(
			os.path.join(self.target, date.strftime('%Y/%m/%d') + '.pickle')
		)

	def transform(self, pickle_keys: list):
		"""

		"""

		new_file = True
		last_datapoint = None

		for kwrd in pickle_keys:
			for idx, datapoint in enumerate(self.csv_reader.yield_rows(dir_or_filename= kwrd)):

				new_day = last_datapoint['date'].date() != datapoint['date'].date()
				new_file = not datapoint or new_day
				if new_file:

					target = self.abspath(datapoint['date'])
					parent = os.path.dirname(target)

					if not os.path.exists(parent): os.makedirs(parent)

					if not os.path.exists(target):  # File not created yet

						# Create datastructure 
						data =  {
							'hours': {
								kwrd: {
									k: [] for k in datapoint.keys()
								}
							}
						}

						# Open and serialize the pickle to disk
						with open(target, 'wb') as f:
							pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
					
					f = open(target, 'rb+')

				if not datapoint or 




if __name__ == "__main__":

	preprocessor = Preprocessor()

	keys = [
		os.path.splitext(filename)
		for filename in os.listdir(
			os.path.join(os.path.dirname(__file__), 'pumpedata') 
		)
	] + ['vaerdata']

	preprocessor.transform(pickle_keys=keys)