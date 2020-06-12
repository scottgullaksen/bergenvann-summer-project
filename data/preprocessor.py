import os
import csv
import logging
import logging.config
import yaml

with open('./logging.yaml', 'r') as f:
	log_cfg = yaml.safe_load(f.read())

logging.config.dictConfig(log_cfg)

logger = logging.getLogger(__name__)


class CSVFileReader(object):

	def __init__(self, path= None):

		# Set path to raw corpus
		path = os.path.join(__file__, path) if not path else path

		# Get all filepaths in dir if path is a dir
		if os.path.isdir(path):
			self.paths = [
				os.path.join(filepath)
				for filepath in os.listdir(path) if os.path.isfile(
					os.path.join(path, filepath)
				)
			]
		else: self.paths = [path]

		# Extract only csv files
		self.paths = filter(lambda f: os.path.splitext(f)[1] == 'csv', self.path)

		if len(self.path) == 0:
			raise ValueError("The provided directory/file contained no csv files")
	
	def yield_rows(self, p):
		for path in self.paths:
			with open(path) as csvfile:
				dataset = csv.reader(csvfile, delimitter= ',')
