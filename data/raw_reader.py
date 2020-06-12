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

		self.logger = logging.getLogger('dev')
		self.logger.setLevel(logging.INFO)

		# Set path to raw corpus
		self.root = os.path.join(
			os.path.dirname(os.path.abspath(__file__)), 'raw_data'
		) if not path else path

		self.logger.info(f'Instantiating with path: {self.root}')

		# Get all filepaths in dir if path is a dir
		self.paths = [
			os.path.join(os.path.abspath(dirpath), filename)
			for dirpath, dirnames, filenames in os.walk(self.root)
			for filename in filenames if os.path.splitext(filename)[1] == '.csv'
		] if os.path.isdir(self.root) else [self.root]

		self.logger.info(f'csv files found: {list(map( lambda f: os.path.basename(f), self.paths))}')

		if len(self.paths) == 0:
			raise ValueError("The provided directory/file contained no csv files")
	
	def yield_all_rows(self, dir_or_filename= None):
		"""
		Returns each row from the csv file or dir specified. Generator.
		"""
		# Return everything uunder root if nothing is specified
		if not dir_or_filename: dir_or_filename = os.path.dirname(self.root)

		for path in self.paths:
			if dir_or_filename in path:
				with open(path) as csvfile:
					dataset = csv.reader(
						csvfile,
						delimiter= '\t' if (  # Choose delimiter based on content of file
							csvfile.readline().count('\t') > csvfile.readline().count(';')
						) else ';'
					)
					for row in dataset:
						yield row

	def get_row(self, i, dir_or_filename):
		for idx, row in enumerate(self.yield_all_rows(dir_or_filename= dir_or_filename)):
			if idx == i:
				return row

if __name__ == '__main__':

	path = os.path.join(
		os.path.dirname(os.path.abspath(__file__)), 'raw_data', 'vaerdata' , 'florida_01.01.11-31.12.13.csv'
	)

	reader = CSVFileReader(path)

	counter = 0
	for row in reader.yield_rows():
		if counter == 10: break
		counter += 1
		print(row)