import os
import csv
import logging
import logging.config
import yaml
from datetime import datetime

with open('./project/logging.yaml', 'r') as f:
    log_cfg = yaml.safe_load(f.read())

logging.config.dictConfig(log_cfg)

class CSVFileReader(object):
    """
    Reades all csv files under path.

    Args:
        path: if not specified, creates relative path to ..this_file/raw_data

    Thought to self: Make this an interface/abstract class?
    Specify required input to preprocessor class -> Should either
    do cleaning here or specify a cleaning (lambda) function to be used in
    preprocessor
    """

    def __init__(self, path: os.path = None):

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
        ] if os.path.isdir(self.root) else [self.root]  # use filter function instead

        self.logger.info(f'csv files found: {list(map(os.path.basename, self.paths))}')

        if len(self.paths) == 0:
            raise ValueError("The provided directory/file contained no csv files")

    def read_datapoints_from(self, reader, cleaner, dir_or_filename= None):
        """
        Yields processed/cleaned datapoints from the csv files under
        dir_or_filenmae.
        
        Args:
            reader: callback that accepts a file object and returns a
            itereable of the rows in the file
            
            cleaner: callback that accepts individual rows from reader
            and returns a processed/cleaned datastructure from it.
        """
        # Return everything under root if nothing is specified
        if not dir_or_filename: dir_or_filename = os.path.dirname(self.root)

        for path in self.paths:
            if dir_or_filename in path:  # Only return contents of relevant files
                with open(path) as csvfile:
                    for row in reader(csvfile):
                        try:
                            yield cleaner(row)
                        except Exception as e:
                            self.logger.warning(f'raw data: {row} could not be dealt with')
                            print(e)

#-------------Cleaners and Readers to be used in above function-------------------------------------------------

def pump_reader(f): return csv.reader(f, delimiter= '\t')

def weather_reader(f): return csv.DictReader(f, delimiter= ';')

def tide_reader(f): return csv.reader(f, delimiter= ' ')

def pump_cleaner(row: list): return {
    'date': datetime.strptime(row[0], '%Y-%m-%d %H:%M'),
    'quantity (l/s)': float(row[2].replace(',', '.')),
    'level (m)': float(row[4].replace(',', '.'))
}

def florida_cleaner(row: list): return {
    'date': datetime.strptime(row['Tid(norsk normaltid)'], '%d.%m.%Y %H:%M'),
    'temp (C)': float(row['Lufttemperatur'].replace(',', '.'))
        if any(c.isnumeric() for c in row['Lufttemperatur']) else None,
    'precipitation (mm)': float(row['NedbÃ¸r (1 t)'].replace(',', '.'))
        if any(c.isnumeric() for c in row['NedbÃ¸r (1 t)']) else 0.0
}

def florida_uib_cleaner(row: list): return {  # Only contains precipitation data
    'date': datetime.strptime(row['Tid(norsk normaltid)'], '%d.%m.%Y %H:%M'),
    'precipitation (mm)': float(row['NedbÃ¸r (1 t)'].replace(',', '.'))
        if any(c.isnumeric() for c in row['NedbÃ¸r (1 t)']) else 0.0
}

def snowdepth_cleaner(row: list): return {
    'date': datetime.strptime(row['Tid(norsk normaltid)'], '%d.%m.%Y'),
    'snodybde (cm)': int(row['SnÃ¸dybde'])
}

def tide_cleaner(row: list):
    return {
    'date': datetime.fromisoformat(row[0]).replace(tzinfo= None),
    'level (cm)': float(row[3] or row[4] or row[5]) # Use the non-empty element
    }

if __name__ == '__main__':

    reader = CSVFileReader()

    counter = 0
    for row in reader.read_datapoints_from(weather_reader, florida_uib_cleaner, 'florida_uib'):
        if counter == 10: break
        counter += 1
        print(row)