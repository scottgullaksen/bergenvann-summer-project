from datetime import datetime, timedelta
import os

def abspath(path, date: datetime):
	"""
	Returns the absolute target file path for the specified date 
	relative to the provided path
	"""
	return os.path.normpath(
		os.path.join(path, date.strftime('%Y/%m/%d') + '.pickle')
	)

def find_first_filepath(path: os.path):
	for dirpath, dirname, filenames in os.walk(path):
		for filename in filenames:
			return os.path.join(dirpath, filename)

def find_last_filepath(path):
	if os.path.isfile(path):
		return path
	return find_last_filepath(os.path.join(path, max(os.listdir(path), lambda c: int(c))))

def path_to_date(relpath, path):
	return datetime.strptime(
		os.path.splitext(os.path.relpath(relpath, path), '%Y/%m/%d')
	)