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

	def save(self, target, data):
		with open(target, 'wb') as f:
			pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

	def load(self, target):
		parent = os.path.dirname(target)
		if not os.path.exists(parent): os.makedirs(parent)

		if not os.path.exists(target): # File not created yet
			return { 'hours': { } } # Create datastructure 

		with open(target, 'rb') as f:
			return pickle.load(f)

	def transform(self, pickle_keys: list):
		"""
		"""
		last_datapoint = None

		for kwrd in pickle_keys:
			for datapoint in self.csv_reader.yield_rows(dir_or_filename= kwrd):

				# Open a new file if first time through loop or new day
				if not last_datapoint or last_datapoint['date'].date() != datapoint['date'].date():

					# Save modified datastructure if not first time trough loop
					if last_datapoint: self.save(target, data)

					target = self.abspath(datapoint['date'])

					data = self.load(target)

				if kwrd in data['hours']:
					for k in datapoint.keys():
						data['hours'][kwrd][k].append(datapoint[k])
				else:
					data['hours'][kwrd] = { k: [v] for k, v in datapoint.items() }

		self.save(target, data)

if __name__ == "__main__":

	preprocessor = Preprocessor()

	keys = [
		os.path.splitext(filename)
		for filename in os.listdir(
			os.path.join(os.path.dirname(__file__), 'pumpedata') 
		)
	] + ['vaerdata']

	preprocessor.transform(pickle_keys=keys)