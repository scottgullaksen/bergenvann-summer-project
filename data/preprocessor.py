import logging
import os
from datetime import datetime
import pickle
from util import abspath

class Preprocessor(object):
	"""
	Wrapper for raw reader class. Preprocceses the files/datapoints, 
	and creates and places into organised file structure. This is a convinient
	place to place heavy time/memory consuming preprocessing functions to
	the data such as aggregation, frequency analysis, etc. 

	Args:
		reader (object): The reader object to be wrapped. Provides reading capabilities to the dataset

		target_dir: path to directory where preprocessed files will be placed. If not
		specified it will create one in the same dir as this module.
	"""
	def __init__(self, reader, target_dir: os.path= None):

		self.logger = logging.getLogger('dev')
		self.logger.setLevel(logging.INFO)

		self.reader = reader

		self.target = os.path.join(
			os.path.dirname(os.path.abspath(__file__)), 'pickled_data'
		) if not target_dir else target_dir

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
		Places all datapoints read from reader into files given by the path:
		target_dir/[year]/[month]/[day].pickle

		The file is pickled dictionary with pickle_keys as keys

		Args:
			pickle_keys: Must be a filename or directory on the path to the
			raw dataset. Distributes the datapoints under that directory/file in the 
			corresponding pickled date dictionary stored under the pickle key.
		"""
		last_datapoint = None

		for kwrd in pickle_keys:
			for datapoint in self.reader.read_datapoints_from(dir_or_filename= kwrd):

				# Open a new file if first time through loop or new day
				if not last_datapoint or last_datapoint['date'].date() != datapoint['date'].date():

					# Save modified datastructure if not first time trough loop
					if last_datapoint != None: self.save(target, data)

					target = abspath(self.target, datapoint['date'])

					data = self.load(target)

				if kwrd in data['hours']:
					for k in datapoint.keys():
						data['hours'][kwrd][k].append(datapoint[k])
				else:
					data['hours'][kwrd] = { k: [v] for k, v in datapoint.items() }
				
				last_datapoint = datapoint

		self.save(target, data)

# Run to create pickled, preprocessed data folder
if __name__ == "__main__":
	from raw_reader import CSVFileReader
	from util import keys

	csv_reader = CSVFileReader()

	preprocessor = Preprocessor(reader=csv_reader)

	preprocessor.transform(pickle_keys=keys)