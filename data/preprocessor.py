import os
import csv
import logging
import logging.config
import yaml

with open('./logging.yaml', 'r') as f:
	log_cfg = yaml.safe_load(f.read())

logging.config.dictConfig(log_cfg)


class CSVFileReader(object):

	def __init__(self, path= None):

		logger = logging.getLogger(__name__)

		# Set path to raw corpus
		path = os.path.join(
			os.path.dirname(os.path.abspath(__file__)), 'raw_data'
		) if not path else path

		print(path)

		logger.info(f'Instantiating with path: {path}')

		# Get all filepaths in dir if path is a dir
		self.paths = [
			os.path.join(os.path.abspath(dirpath), filename)
			for dirpath, dirnames, filenames in os.walk(path)
			for filename in filenames if os.path.splitext(filename)[1] == '.csv'
		] if os.path.isdir(path) else [path]

		print(self.paths)

		logger.info(f'csv files found: {self.paths}')

		if len(self.paths) == 0:
			raise ValueError("The provided directory/file contained no csv files")
	
	def yield_rows(self, p):
		for path in self.paths:
			with open(path) as csvfile:
				dataset = csv.reader(csvfile, delimitter= ',')


if __name__ == '__main__':

	path = os.path.join(
		os.path.dirname(os.path.abspath(__file__)), 'raw_data', 'pumpedata' , 'GeorgernesVerft.csv'
	)

	reader = CSVFileReader(path)