from datetime import datetime, timedelta
import os

keys = [
	os.path.splitext(filename)[0]
	for filename in os.listdir(
		os.path.normpath(
			os.path.join(os.path.dirname(__file__), 'raw_data/pumpedata') 
		)
	) if os.path.splitext(filename)[1] == '.csv'
] + ['vaerdata']

def abspath(path, date: datetime):
	"""
	Returns the absolute target file path for the specified date 
	relative to the provided path
	"""
	return os.path.normpath(
		os.path.join(path, date.strftime('%Y/%m/%d') + '.pickle')
	)

def find_first_filepath(path: os.path) -> os.path:
	for dirpath, dirname, filenames in os.walk(path):
		for filename in filenames:
			return os.path.join(dirpath, filename)

def find_last_filepath(path: os.path) -> os.path:
	if os.path.isfile(path):
		return path
	return find_last_filepath(
		os.path.join(
			path,
			max(os.listdir(path), key= lambda c: int(c) if c.isnumeric() else int(
				os.path.splitext(c)[0]
			))
		)
	)

def string_range(first: int, last: int):
	"""Create a string representation of the range"""
	return [
		f'0{i}' if i < 10 else str(i) for i in range(first, last + 1)
	]